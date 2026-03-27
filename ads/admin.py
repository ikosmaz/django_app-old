from django.contrib import admin
from ads.models import Ad, CommentFav, Fav, Message

# Register your models here.

class PicAdmin(admin.ModelAdmin):
    exclude = ('picture', 'content_type')

admin.site.register(Ad, PicAdmin)

admin.site.register(Fav)

admin.site.register(CommentFav)
admin.site.register(Message)
