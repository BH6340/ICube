#!/bin/bash
# 生成 APK 签名 keystore
# 用法：bash scripts/generate-keystore.sh
# 生成后按提示将 keystore 信息填入 android/keystore.properties

KEYSTORE_FILE="android/icube.jks"
KEY_ALIAS="icube"
KEYSTORE_PASS=$(openssl rand -base64 16 | tr -d '+/=' | head -c 20)
KEY_PASS=$(openssl rand -base64 16 | tr -d '+/=' | head -c 20)

echo "正在生成 keystore..."
keytool -genkeypair \
  -alias "$KEY_ALIAS" \
  -keyalg RSA \
  -keysize 2048 \
  -validity 36500 \
  -keystore "$KEYSTORE_FILE" \
  -storepass "$KEYSTORE_PASS" \
  -keypass "$KEY_PASS" \
  -dname "CN=ICube, OU=Dev, O=ICube, L=Shanghai, ST=Shanghai, C=CN"

if [ $? -ne 0 ]; then
  echo "生成失败，请检查 keytool 是否可用"
  exit 1
fi

cat > android/keystore.properties << EOF
storeFile=icube.jks
storePassword=$KEYSTORE_PASS
keyAlias=$KEY_ALIAS
keyPassword=$KEY_PASS
EOF

echo ""
echo "keystore 已生成：$KEYSTORE_FILE"
echo "配置已写入：android/keystore.properties"
echo ""
echo "如需配置 CI/CD，请执行以下步骤："
echo "1. base64 编码 keystore："
echo "   base64 -w 0 $KEYSTORE_FILE"
echo ""
echo "2. 在 GitHub 仓库 Settings → Secrets and variables → Actions 中添加："
echo "   KEYSTORE_BASE64     = 上面的 base64 字符串"
echo "   KEYSTORE_PASSWORD   = $KEYSTORE_PASS"
echo "   KEY_ALIAS           = $KEY_ALIAS"
echo "   KEY_PASSWORD         = $KEY_PASS"
echo "   SERVER_SSH_KEY       = 服务器 SSH 私钥"
echo "   SERVER_HOST         = 服务器地址"
echo "   SERVER_USER         = SSH 用户名"
