from django.conf import settings


def build_image_url(relative_path, absolute=False):
    """
    生成统一的图片URL
    
    Args:
        relative_path: 图片相对路径，如 '/media/avatars/user.png' 或 'forum/posts/2024/01/image.png'
        absolute: 是否返回绝对URL（用于邮件等场景），默认返回相对路径以避免CORS问题
    
    Returns:
        图片URL（默认相对路径，absolute=True时返回完整绝对URL）
    """
    if not relative_path:
        return ''
    
    if hasattr(relative_path, 'path'):
        relative_path = str(relative_path)
    
    if relative_path.startswith('http://') or relative_path.startswith('https://'):
        return relative_path
    
    if not relative_path.startswith('/'):
        relative_path = '/' + relative_path
    
    if not relative_path.startswith('/media/'):
        relative_path = '/media' + relative_path
    
    if absolute:
        return settings.SITE_DOMAIN.rstrip('/') + relative_path
    
    return relative_path