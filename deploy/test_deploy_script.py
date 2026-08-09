from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_SCRIPT = PROJECT_ROOT / "deploy.sh"


class DeployScriptContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = DEPLOY_SCRIPT.read_text(encoding="utf-8")

    def test_uses_safe_shell_and_fast_forward_pull(self):
        self.assertIn("set -Eeuo pipefail", self.content)
        self.assertIn("git pull --ff-only", self.content)

    def test_allows_deployment_with_tracked_file_changes(self):
        self.assertNotIn(
            "git status --porcelain --untracked-files=no",
            self.content,
        )
        self.assertNotIn(
            "检测到已跟踪文件存在本地修改",
            self.content,
        )

    def test_never_deletes_volumes_or_overwrites_git_history(self):
        self.assertNotIn("down -v", self.content)
        self.assertNotIn("git reset --hard", self.content)
        self.assertNotIn("init_data.sql", self.content)

    def test_migrates_old_media_and_preserves_backup(self):
        self.assertIn('OLD_MEDIA_DIR="$PROJECT_DIR/media"', self.content)
        self.assertIn('NEW_MEDIA_DIR="$PROJECT_DIR/cube_api/media"', self.content)
        self.assertIn("media-before-migration-", self.content)

    def test_preserves_target_media_before_merging_legacy_media(self):
        self.assertIn("media-target-before-migration-", self.content)
        target_backup_position = self.content.index(
            'cp -a "$NEW_MEDIA_DIR/." "$target_backup_dir/"'
        )
        legacy_copy_position = self.content.index(
            'cp -a "$OLD_MEDIA_DIR/." "$NEW_MEDIA_DIR/"'
        )

        self.assertLess(target_backup_position, legacy_copy_position)

    def test_builds_migrates_and_starts_services(self):
        self.assertIn("compose build --pull", self.content)
        self.assertIn("compose stop api", self.content)
        self.assertIn("compose up -d db redis", self.content)
        self.assertIn(
            "compose run --rm --no-deps api python manage.py migrate --noinput",
            self.content,
        )
        self.assertIn("compose up -d", self.content)

    def test_reports_logs_on_failure_and_verifies_http(self):
        self.assertIn("trap 'on_error $LINENO' ERR", self.content)
        self.assertIn("compose logs --no-color --tail=100", self.content)
        self.assertIn('ICUBE_HEALTHCHECK_HOST', self.content)
        self.assertIn(
            'HEALTHCHECK_HOST="${ICUBE_HEALTHCHECK_HOST:-${ALLOWED_HOSTS:-}}"',
            self.content,
        )
        self.assertIn('-H "Host: $HEALTHCHECK_HOST"', self.content)
        self.assertIn("http://127.0.0.1/", self.content)
        self.assertIn(
            "http://127.0.0.1/api/home/banners/",
            self.content,
        )
        self.assertIn("compose exec -T redis redis-cli ping", self.content)

    def test_stops_api_before_media_copy_and_database_migration(self):
        self.assertIn("compose stop api", self.content)
        stop_position = self.content.index("compose stop api")
        media_copy_position = self.content.index(
            'cp -a "$OLD_MEDIA_DIR/." "$NEW_MEDIA_DIR/"'
        )
        migration_position = self.content.index(
            "compose run --rm --no-deps api python manage.py migrate --noinput"
        )

        self.assertLess(stop_position, media_copy_position)
        self.assertLess(stop_position, migration_position)


if __name__ == "__main__":
    unittest.main()
