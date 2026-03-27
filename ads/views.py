from ads.models import Ad, Comment, Fav, CommentFav, Message
from ads.owner import OwnerListView, OwnerDetailView, OwnerCreateView, OwnerUpdateView, OwnerDeleteView
from django.views import View
from django.views.generic import ListView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.uploadedfile import InMemoryUploadedFile
from ads.forms import CreateForm, CommentForm, MessageForm, NewUserForm
from django.contrib.humanize.templatetags.humanize import naturaltime
from ads.utils import dump_queries
from django.db.models import Q

from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm

# Create your views here.
def register_request(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Registration successful.")
            return redirect("ads:all")
        messages.error(request, "Unsuccessful registration. Please fix the errors below.")
    else:
        form = NewUserForm()
    return render(request=request, template_name="ads/register.html", context={"register_form": form})

def login_request(request):
	if request.method == "POST":
		form = AuthenticationForm(request, data=request.POST)
		if form.is_valid():
			username = form.cleaned_data.get('username')
			password = form.cleaned_data.get('password')
			user = authenticate(username=username, password=password)
			if user is not None:
				login(request, user)
				messages.info(request, f"You are now logged in as {username}.")
				return redirect("ads:all")
			else:
				messages.error(request,"Invalid username or password.")
		else:
			messages.error(request,"Invalid username or password.")
	form = AuthenticationForm()
	return render(request=request, template_name="accounts/login.html", context={"login_form":form})

class AdListView(OwnerListView):
    model = Ad
    # By convention:
    template_name = "ads/ad_list.html"

    def get(self, request) :
        ad_list = Ad.objects.all()
        favorites = list()

        strval =  request.GET.get("search", False)
        if strval :
            # Simple title-only search
            # objects = Post.objects.filter(title__contains=strval).select_related().order_by('-updated_at')[:10]
            # Multi-field search
            # __icontains for case-insensitive search
            query = Q(title__icontains=strval)
            query.add(Q(text__icontains=strval), Q.OR)
            ad_list = Ad.objects.filter(query).select_related().order_by('-updated_at')[:20]
        else :
            ad_list = Ad.objects.all().order_by('-updated_at')[:20]

        # Augment the post_list
        for obj in ad_list:
            obj.natural_updated = naturaltime(obj.updated_at)

        if request.user.is_authenticated:
            # rows = [{'id': 2}, {'id': 4} ... ]  (A list of rows)
            rows = request.user.favorite_ads.values('id')
            # favorites = [2, 4, ...] using list comprehension
            favorites = [ row['id'] for row in rows ]
            favorites_count = len(favorites)
            my_ads_count = Ad.objects.filter(owner=request.user).count()
        else:
            favorites = []
            favorites_count = 0
            my_ads_count = 0

        ctx = {
            'ad_list': ad_list,
            'favorites': favorites,
            'favorites_count': favorites_count,
            'my_ads_count': my_ads_count,
            'search': strval
        }
        retval= render(request, self.template_name, ctx)

        dump_queries()
        return retval


class AdDetailView(OwnerDetailView):
    model = Ad
    template_name = "ads/ad_detail.html"

    def get(self, request, pk) :
        x = get_object_or_404(Ad, id=pk)
        comments = Comment.objects.filter(ad=x).select_related('owner').order_by('-updated_at')
        comment_form = CommentForm()
        message_form = MessageForm()
        message_threads = []
        ad_unread_messages_count = 0

        favorites = []
        comment_favorites = []
        all_comments_count = comments.count()
        liked_comments_count = 0
        comment_filter = request.GET.get('comments', 'all')

        if request.user.is_authenticated:
            favorites = [row['id'] for row in request.user.favorite_ads.values('id')]
            comment_favorites = [
                row['id'] for row in request.user.favorite_comments.filter(ad=x).values('id')
            ]
            liked_comments_count = len(comment_favorites)
            if comment_filter == 'liked':
                comments = comments.filter(id__in=comment_favorites)

            message_query = Message.objects.filter(ad=x).select_related('sender', 'recipient', 'ad', 'parent')
            if request.user == x.owner:
                ad_messages = list(message_query.order_by('created_at'))
            else:
                ad_messages = list(message_query.filter(
                    Q(sender=request.user) | Q(recipient=request.user)
                ).order_by('created_at'))

            thread_map = {}
            thread_order = []
            for msg in ad_messages:
                other_user = msg.sender if msg.sender != request.user else msg.recipient
                if other_user.id not in thread_map:
                    thread_map[other_user.id] = {
                        'user': other_user,
                        'messages': [],
                    }
                    thread_order.append(other_user.id)
                thread_map[other_user.id]['messages'].append(msg)

            message_threads = [thread_map[user_id] for user_id in thread_order]
            ad_unread_messages_count = sum(
                1 for m in ad_messages if (m.recipient_id == request.user.id and not m.is_read)
            )

            Message.objects.filter(
                id__in=[m.id for m in ad_messages],
                recipient=request.user,
                is_read=False
            ).update(is_read=True)
        else:
            comment_filter = 'all'

        context = {
            'ad': x,
            'comments': comments,
            'comment_form': comment_form,
            'favorites': favorites,
            'comment_favorites': comment_favorites,
            'comment_filter': comment_filter,
            'all_comments_count': all_comments_count,
            'liked_comments_count': liked_comments_count,
            'message_threads': message_threads,
            'ad_unread_messages_count': ad_unread_messages_count,
            'message_form': message_form,
        }
        return render(request, self.template_name, context)


class AdCreateView(OwnerCreateView):
    model = Ad
    #fields = ['title','price','text', 'picture']
    template_name = 'ads/ad_form.html'
    success_url = reverse_lazy('ads:all')

    def get(self, request, pk=None):
        form = CreateForm()
        ctx = {'form': form}
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        form = CreateForm(request.POST, request.FILES or None)

        if not form.is_valid():
            ctx = {'form': form}
            return render(request, self.template_name, ctx)

        # Add owner to the model before saving
        ad = form.save(commit=False)
        ad.owner = self.request.user
        ad.save()
        return redirect(self.success_url)



class AdUpdateView(OwnerUpdateView):
    model = Ad
    #fields = ['title','price','text', 'picture']
    template_name = 'ads/ad_form.html'
    success_url = reverse_lazy('ads:all')

    def get(self, request, pk):
        ad = get_object_or_404(Ad, id=pk, owner=self.request.user)
        form = CreateForm(instance=ad)
        ctx = {'form': form}
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        ad = get_object_or_404(Ad, id=pk, owner=self.request.user)
        form = CreateForm(request.POST, request.FILES or None, instance=ad)

        if not form.is_valid():
            ctx = {'form': form}
            return render(request, self.template_name, ctx)

        ad = form.save(commit=False)
        ad.save()

        return redirect(self.success_url)


class AdDeleteView(OwnerDeleteView):
    model = Ad
    template_name = "ads/ad_confirm_delete.html"

def stream_file(request, pk):
    ad = get_object_or_404(Ad, id=pk)
    response = HttpResponse()
    response['Content-Type'] = ad.content_type
    response['Content-Length'] = len(ad.picture)
    response.write(ad.picture)
    return response

class CommentCreateView(LoginRequiredMixin, View):
    def post(self, request, pk) :
        ad = get_object_or_404(Ad, id=pk)
        form = CommentForm(request.POST)
        if form.is_valid():
            Comment.objects.create(
                text=form.cleaned_data['text'],
                owner=request.user,
                ad=ad
            )
        return redirect(reverse_lazy('ads:ad_detail', args=[pk]))

class CommentDeleteView(OwnerDeleteView):
    model = Comment
    template_name = "ads/ad_comment_delete.html"

    # https://stackoverflow.com/questions/26290415/deleteview-with-a-dynamic-success-url-dependent-on-id
    def get_success_url(self):
        ad = self.object.ad
        return reverse_lazy('ads:ad_detail', args=[ad.id])


class MessageCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        ad = get_object_or_404(Ad, id=pk)
        if ad.owner == request.user:
            return redirect(f"{reverse('ads:ad_detail', args=[pk])}#messages-panel")

        form = MessageForm(request.POST)
        if form.is_valid():
            message = Message(
                ad=ad,
                sender=request.user,
                recipient=ad.owner,
            )
            message.set_text(form.cleaned_data['encrypted_text'])
            message.save()

        return redirect(f"{reverse('ads:ad_detail', args=[pk])}#messages-panel")


class MessageReplyView(LoginRequiredMixin, View):
    def post(self, request, pk):
        source_message = get_object_or_404(Message.objects.select_related('ad', 'sender'), id=pk)
        ad = source_message.ad

        if request.user != ad.owner or source_message.sender == request.user:
            return HttpResponseForbidden('Only the ad owner can reply to incoming messages.')

        form = MessageForm(request.POST)
        if form.is_valid():
            reply = Message(
                ad=ad,
                sender=request.user,
                recipient=source_message.sender,
                parent=source_message,
            )
            reply.set_text(form.cleaned_data['encrypted_text'])
            reply.save()

        return redirect(f"{reverse('ads:ad_detail', args=[ad.id])}#messages-panel")

# csrf exemption in class based views
# https://stackoverflow.com/questions/16458166/how-to-disable-djangos-csrf-validation
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.utils import IntegrityError

@method_decorator(csrf_exempt, name='dispatch')
class AddFavoriteView(LoginRequiredMixin, View):
    def post(self, request, pk) :
        print("Add PK",pk)
        t = get_object_or_404(Ad, id=pk)
        fav = Fav(user=request.user, ad=t)
        try:
            fav.save()  # In case of duplicate key
        except IntegrityError as e:
            pass
        return HttpResponse()

@method_decorator(csrf_exempt, name='dispatch')
class DeleteFavoriteView(LoginRequiredMixin, View):
    def post(self, request, pk) :
        print("Delete PK",pk)
        t = get_object_or_404(Ad, id=pk)
        try:
            fav = Fav.objects.get(user=request.user, ad=t).delete()
        except Fav.DoesNotExist as e:
            pass

        return HttpResponse()


@method_decorator(csrf_exempt, name='dispatch')
class AddCommentFavoriteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        comment = get_object_or_404(Comment, id=pk)
        fav = CommentFav(user=request.user, comment=comment)
        try:
            fav.save()
        except IntegrityError:
            pass
        return HttpResponse()


@method_decorator(csrf_exempt, name='dispatch')
class DeleteCommentFavoriteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        comment = get_object_or_404(Comment, id=pk)
        try:
            CommentFav.objects.get(user=request.user, comment=comment).delete()
        except CommentFav.DoesNotExist:
            pass
        return HttpResponse()


class FavoriteListView(LoginRequiredMixin, ListView):
    model = Ad
    template_name = 'ads/ad_list.html'
    context_object_name = 'ad_list'

    def get_queryset(self):
        return Ad.objects.filter(fav__user=self.request.user).order_by('-updated_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # favorites_count for the badge
        rows = self.request.user.favorite_ads.values('id')
        ctx['favorites_count'] = len(rows)
        ctx['my_ads_count'] = Ad.objects.filter(owner=self.request.user).count()

        # also include the list of favorite IDs, same as in AdListView
        ctx['favorites'] = [row['id'] for row in rows]

        # search param placeholder (your template expects it)
        ctx['search'] = ""

        for obj in ctx['ad_list']:
            obj.natural_updated = naturaltime(obj.updated_at)

        return ctx


class MyAdListView(LoginRequiredMixin, ListView):
    model = Ad
    template_name = 'ads/ad_list.html'
    context_object_name = 'ad_list'

    def get_queryset(self):
        return Ad.objects.filter(owner=self.request.user).order_by('-updated_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        rows = self.request.user.favorite_ads.values('id')
        ctx['favorites_count'] = len(rows)
        ctx['my_ads_count'] = ctx['ad_list'].count() if hasattr(ctx['ad_list'], 'count') else len(ctx['ad_list'])
        ctx['favorites'] = [row['id'] for row in rows]
        ctx['search'] = ""

        for obj in ctx['ad_list']:
            obj.natural_updated = naturaltime(obj.updated_at)

        return ctx
