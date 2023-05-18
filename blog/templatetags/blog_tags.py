from django import template
from django.db.models import Count
from ..models import Post

#tạo biến register từ template library để đăng kí template tags
register = template.Library()

#đăng kí simple_tag với deco register
@register.simple_tag
#tạo hàm total_posts để hiển thị lên base.html dùng để trả về tổng số post đã viết
def total_posts():
    return Post.published.count()

@register.simple_tag
#tạo hàm lấy các bài viết có cmt nhiều nhất (dùng Count), order theo thứ tự giảm dần(-)
def get_most_commented_posts(count=5):
    return Post.published.annotate(total_comments=Count('comments')).order_by('-total_comments')[:count]

#đăng kí inclusion_tag có template là latest_posts.html
@register.inclusion_tag('blog/post/latest_posts.html')
#tạo hàm show_latest_posts hiển thị x posts pulish gần nhất
def show_latest_posts(count=5):
    latest_posts = Post.published.order_by('-publish')[:count]
    return {'latest_posts':latest_posts}
