from django.shortcuts import render, get_object_or_404
from .models import Post
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from .forms import EmailPostForm
from django.core.mail import send_mail

# Create your views here.


# def post_list(request):
#     post_list=Post.published.all()
#     paginator = Paginator(post_list, 3) #đưa các bài trong post_list vào Paginator, và chia thành 3 bài/trang
#     page_number = request.GET.get('page', 1) #dùng get để lấy giá trị trong ?page=
#     try:
#         posts = paginator.page(page_number)
#     except PageNotAnInteger:
#         #Nếu số page là chữ, đưa page về trang 1
#         posts = paginator.page(1)
#     except EmptyPage:
#         #Nếu số page quá số lượng hiện tại thì trả về page cuối
#         posts = paginator.page(paginator.num_pages)
#     return render(request, 'blog/post/list.html', {'posts':posts})

def post_share(request, post_id):
    #lấy thông tin bài viết
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False
    # Kiểm tra nếu có POST -> lấy bản ghi từ request.POST -> kiểm tra nếu bản ghi valid(data cleaned)
    # -> truyền thông tin đó vào cd để gửi mail
    if request.method== 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid:
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url)
            subject = f"{cd['name']} recommends you read {post.title}"
            message = f"read {post.title} at {post_url} \n\n {cd['name']} comments: {cd['comments']}"
            send_mail(subject, message, "ttceen@gmail.com", [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, "blog/post/share.html", {"post":post, "form":form, "sent":sent})

class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_detail(request, year, month, day, post):

    post = get_object_or_404(Post, status=Post.Status.PUBLISHED, slug=post,
                                publish__year=year, publish__month=month, publish__day=day)
    return render(request, 'blog/post/detail.html', {'post':post})


