from django.contrib import admin
from .models import Article, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'created_on']
    list_filter = ['category', 'author', 'created_on']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_on', 'last_modified']
    
    fieldsets = (
        ('Article Content', {
            'fields': ('title', 'slug', 'author', 'category', 'content')
        }),
        ('SEO', {
            'fields': ('meta_description',)
        }),
        ('Timestamps', {
            'fields': ('created_on', 'last_modified'),
            'classes': ('collapse',)
        }),
    )
