from django.conf import settings


def build_image_url(relative_path):
    """
    生成统一的图片URL，不受请求来源影响
    
    Args:
        relative_path: 图片相对路径，如 '/media/avatars/user.png' 或 'forum/posts/2024/01/image.png'
    
    Returns:
        完整的图片URL
    """
    if not relative_path:
        return ''
    
    if relative_path.startswith('http://') or relative_path.startswith('https://'):
        return relative_path
    
    if not relative_path.startswith('/'):
        relative_path = '/' + relative_path
    
    return settings.SITE_DOMAIN.rstrip('/') + relative_path