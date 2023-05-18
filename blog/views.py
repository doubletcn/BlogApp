from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from taggit.models import Tag
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm, SearchForm
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, TrigramSimilarity


# Create your views here.

#tag_slug=None cho phép có thể truyền hoặc không giá trị vào tag_slug
#nếu url là /blog/tag/<slug:tag_slug>/ thì sẽ truyền, còn /blog/ thì không truyền
def post_list(request, tag_slug=None):
    post_list=Post.published.all()
    tag = None
    if tag_slug: #Nếu có tag_slug từ url(tag_slug khác None)
        tag = get_object_or_404(Tag, slug=tag_slug) #lấy tag có trong bảng Tag với slug=tag_slug
        post_list = post_list.filter(tags__in=[tag]) #lấy ra các post có tag=tag

    paginator = Paginator(post_list, 3) #đưa các bài trong post_list vào Paginator, và chia thành 3 bài/trang
    page_number = request.GET.get('page', 1) #dùng get để lấy giá trị trong ?page=
    try :
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        #Nếu số page là chữ, đưa page về trang 1
        posts = paginator.page(1)
    except EmptyPage:
        #Nếu số page quá số lượng hiện tại thì trả về page cuối
        posts = paginator.page(paginator.num_pages)
    return render(request, 'blog/post/list.html', {'posts':posts, 'tag':tag})

def post_share(request, post_id):
    #lấy thông tin bài viết
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False
    # Kiểm tra nếu có POST -> lấy bản ghi từ request.POST -> kiểm tra nếu bản ghi valid(data cleaned)
    # -> truyền thông tin đó vào cd để gửi mail
    if request.method== 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read {post.title}"
            message = f"read '{post.title}' at {post_url} \n\n {cd['name']} comments: {cd['comments']}"
            send_mail(subject, message, "ttceen@gmail.com", [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, "blog/post/share.html", {"post":post, "form":form, "sent":sent})

# class PostListView(ListView):
#     queryset = Post.published.all()
#     context_object_name = 'posts'
#     paginate_by = 3
#     template_name = 'blog/post/list.html'


def post_detail(request, year, month, day, post):

    post = get_object_or_404(Post, status=Post.Status.PUBLISHED, slug=post,
                                publish__year=year, publish__month=month, publish__day=day)
    comments = post.comments.filter(active=True)
    form = CommentForm()
    #sử dụng value_list để lấy 1 tuple gồm các id của tag trong post hiện tại
    post_tags_ids = post.tags.values_list('id', flat=True)
    #sử dụng filter để lọc ra các post có tag id giống các id vừa lấy trừ id post hiện tại
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    #sử dụng hàm Count trong annotate() để đếm số lượng tag trùng nhau sau đó
    # order giảm dần dựa trên số lượng tag chung và ngày phát hành gần đây nhất (lấy 4 post)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]
    #render đến trang detail post cùng các biến context hiện có
    return render(request, 'blog/post/detail.html', {'post':post, 'comments':comments, 'form':form,
                                                     'similar_posts':similar_posts})


# chỉ cho POST request đến view(ko cho GET, PUT, DELETE)
@require_POST
# tạo view post_comment để quản lý comment submit
def post_comment(request, post_id):
    #lấy post từ db với id=id và status=publish
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    # tạo comment = none để lát truyền data vào
    comment = None
    # tạo bản ghi form=CommentForm bằng phương thức submit của post
    form = CommentForm(data=request.POST)
    # kiểm tra xem form có data ko
    if form.is_valid():
        # tạo đối tượng comment, gán data của form vào comment nhưng chưa lưu vào db
        comment = form.save(commit=False)
        # chỉ định bài viết cho comment sau đó mới lưu comment data vào db(post của comment = post)
        comment.post = post
        comment.save()
    #render trang web 'blog/post/comment.html', truyền các đối tượng post, form, comment vào template context
    return render(request, 'blog/post/comment.html', {'post':post, 'form':form, 'comment':comment})

def post_search(request):
    form = SearchForm()
    query = None
    results = []

    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid(): #form valid nghĩa là có "?query=abc-xyz-toi-la-trung..."
            query = form.cleaned_data['query'] #làm sạch query ở trên(bỏ các ký tự, khoảng trắng)

            #search with weight, stemming, rank and stop-words
            search_vector = SearchVector('title', weight='A', config='english') +\
                             SearchVector('body', weight='B', config='english')


            search_query = SearchQuery(query, config='english')
            results = Post.published.annotate(search=search_vector,
                                              rank= SearchRank(search_vector, search_query)
                                              ).filter(rank__gte=0.2).order_by('-rank')

            #search with similarity
            # results = Post.published.annotate(
            #         similarity = TrigramSimilarity('title', query)).filter(similarity__gt=0.1).order_by('-similarity')
    return render(request, 'blog/post/search.html', {'form':form, 'query':query, 'results':results})

