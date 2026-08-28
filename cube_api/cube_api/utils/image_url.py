# -*- coding: utf-8 -*-
"""
图片 URL 生成工具

该模块提供统一的图片路径处理函数，确保图片 URL 在前端和后端之间的一致性。

设计背景：
    - 项目中图片存储路径存在多种格式（有无 /media/ 前缀）
    - 直接对 Django ImageFieldFile 对象调用字符串方法会引发 AttributeError
    - 浏览器 Private Network Access (PNA) 策略会阻止公网域名直接访问 localhost 图片
    - 需要支持相对路径（前端展示）和绝对路径（邮件等场景）两种模式

核心函数：
    - build_image_url: 生成统一的图片URL
"""
from django.conf import settings


def build_image_url(relative_path, absolute=False):
    """
    生成统一的图片URL

    该函数处理多种输入格式，确保输出标准化的图片路径。
    主要解决以下问题：
    1. Django ImageFieldFile 对象需要先转换为字符串
    2. 路径前缀不一致（有无 /media/）
    3. 已有的绝对URL需要原样返回
    4. 支持相对路径和绝对路径两种输出模式

    Args:
        relative_path: 图片相对路径，可能的格式包括：
            - Django ImageFieldFile 对象（需转换）
            - 完整绝对URL（如 http://example.com/media/image.png）
            - 带 /media/ 前缀的相对路径（如 /media/avatars/user.png）
            - 不带 /media/ 前缀的相对路径（如 forum/posts/2024/01/image.png）
        absolute: 是否返回绝对URL。默认为 False，返回相对路径以避免 CORS/PNA 问题；
                  设置为 True 时，会拼接 SITE_DOMAIN 生成完整绝对URL（用于邮件等场景）

    Returns:
        标准化的图片URL。默认返回相对路径（如 /media/avatars/user.png），
        absolute=True 时返回完整绝对URL（如 http://localhost:8000/media/avatars/user.png）

    Examples:
        >>> build_image_url('/media/avatars/user.png')
        '/media/avatars/user.png'
        
        >>> build_image_url('forum/posts/image.png')
        '/media/forum/posts/image.png'
        
        >>> build_image_url(image_field_file_object)
        '/media/formulas/F2L_001.png'
        
        >>> build_image_url('/media/image.png', absolute=True)
        'http://localhost:8000/media/image.png'
    """
    # 边界条件：空路径直接返回空字符串
    if not relative_path:
        return ''
    
    # 关键处理：Django ImageFieldFile 对象不能直接调用字符串方法
    # hasattr(relative_path, 'path') 用于判断是否为文件对象
    # 需要先转换为字符串才能继续处理
    # 注意：hasattr 会触发 .path 属性访问，可能导致 SuspiciousFileOperation
    # 所以改用 isinstance 判断，或者捕获异常
    try:
        from django.db.models.fields.files import FieldFile
        if isinstance(relative_path, FieldFile):
            # 直接用 name 属性，避免触发 path 属性的计算
            if relative_path.name:
                relative_path = relative_path.name
            else:
                return ''
    except ImportError:
        # 如果导入失败，尝试转换为字符串
        try:
            relative_path = str(relative_path)
        except (ValueError, TypeError, AttributeError):
            return ''
    else:
        # 如果没有抛出 ImportError，还需要检查是否能成功转换为字符串
        if not isinstance(relative_path, str):
            try:
                relative_path = str(relative_path)
            except (ValueError, TypeError, AttributeError):
                return ''
    
    # 如果已经是完整的绝对URL，直接返回，无需处理
    if relative_path.startswith('http://') or relative_path.startswith('https://'):
        return relative_path
    
    # 确保路径以 / 开头，便于后续拼接
    if not relative_path.startswith('/'):
        relative_path = '/' + relative_path
    
    # 统一添加 /media/ 前缀
    # 数据库中存储的图片路径可能有两种格式：
    # 1. '/media/avatars/user.png'（已带前缀）
    # 2. '/avatars/user.png'（不带前缀）
    # 这里统一处理为带 /media/ 前缀的格式
    if not relative_path.startswith('/media/'):
        relative_path = '/media' + relative_path
    
    # 根据参数决定返回相对路径还是绝对路径
    # 默认返回相对路径，避免浏览器 PNA 策略阻止访问
    # 仅在需要发送邮件等场景下使用绝对路径
    if absolute:
        return settings.SITE_DOMAIN.rstrip('/') + relative_path
    
    return relative_path
