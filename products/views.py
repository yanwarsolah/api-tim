import http
import json

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from payload_wtf import pwtf

from app.commons.decorators import auth_with_token
from app.commons.views import paginators
from app.commons.views.bodyparsers import json_parser
from products.facade_filter import FacadeCategoryFilter
from products.models import Category, Product


class CategoryListView(View):

    model = Category
    payload = pwtf.PayloadWTF()
    paging = paginators
    facade = FacadeCategoryFilter

    @method_decorator(csrf_exempt)
    @method_decorator(auth_with_token)
    def dispatch(self, *args, **kwargs):
        return super(CategoryListView, self).dispatch(*args, **kwargs)

    def get_queryset(self, request):
        categories = self.model.objects.all()
        facade = self.facade(categories)
        facade.filter_by_id(request.GET.get('id', ''))
        facade.filter_by_name(request.GET.get('name', ''))

        return facade.get_result()

    def get(self, request):
        categories = self.get_queryset(request)
        # Select mode is true if you have search selectable on frontend.
        select_mode = request.GET.get('select_mode')
        if not select_mode:
            categories, self.payload = self.paging.paginate(request, categories, self.payload, 3)

        data = []
        for category in categories:
            data.append({
                'id': category.id,
                'name': category.name
            })

        self.payload.set_state(setter=self.payload.SET_RESULT, data=data)
        return JsonResponse(self.payload.todata(), safe=False, status=http.HTTPStatus.OK)

    def post(self, request):
        body = json.loads(request.body.decode('utf-8'))
        Category.objects.create(name=body.get('name'))
        self.payload.reset()
        self.payload.set_state(setter=self.payload.SET_RESULT, data={'message': 'Success create data'})

        return JsonResponse(self.payload.todata(), safe=False, status=http.HTTPStatus.CREATED)


class CategoryDetailView(View):
    model = Category
    payload = pwtf.PayloadWTF()

    @method_decorator(csrf_exempt)
    @method_decorator(auth_with_token)
    def dispatch(self, *args, **kwargs):
        return super(CategoryDetailView, self).dispatch(*args, **kwargs)

    def get_object(self, pk):
        return get_object_or_404(self.model, pk=pk)

    def get(self, request, pk):
        category = self.get_object(pk)
        self.payload.set_state(setter=self.payload.SET_RESULT, data={
            'id': category.id,
            'name': category.name
        })

        return JsonResponse(self.payload.todata(), safe=False, status=http.HTTPStatus.OK)

    def put(self, request, pk):
        body = json_parser(request)

        category = self.get_object(pk)
        category.name = body.get('name')
        category.save()

        self.payload.reset()
        self.payload.set_state(setter=self.payload.SET_RESULT, data={'message': 'Success update category'})

        return JsonResponse(self.payload.todata(), safe=False, status=http.HTTPStatus.OK)

    def delete(self, request, pk):
        category = self.get_object(pk)
        category.delete()

        self.payload.reset()
        self.payload.set_state(setter=self.payload.SET_RESULT, data={'message': 'Success delete category'})

        return JsonResponse(self.payload.todata(), safe=False, status=http.HTTPStatus.NO_CONTENT)


@csrf_exempt
@auth_with_token
def product_list(request):
    if request.method == 'GET':
        payload = {'results': [], 'links': {'next': '', 'prev': ''}, 'meta': {}}
        page = request.GET.get('page', 1)
        name = request.GET.get('name', '')

        products = Product.objects.all()

        if name:
            products = products.filter(name__contains=name)

        paginator = Paginator(products, 1)

        try:
            products = paginator.page(page)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)

        for product in products:
            payload['results'].append({
                'id': product.id,
                'name': product.name,
                'category': {
                    'id': product.category.id,
                    'name': product.category.name
                },
                'category_human': product.category.name,
                'stock': product.stock,
                'stock_minimum': product.stock_minimum,
                'price': product.price
            })

        if products.has_previous():
            payload['links']['prev'] = products.previous_page_number()

        if products.has_next():
            payload['links']['next'] = products.next_page_number()

        return JsonResponse(payload, safe=False, status=http.HTTPStatus.OK)


@csrf_exempt
@auth_with_token
@require_http_methods(["POST"])
def product_add(request):
    payload = {'results': {'message': ''}, 'meta': {}, 'links': {'next': '', 'prev': ''}}
    body = json.loads(request.body.decode('utf-8'))
    category = Category.objects.get(id=body.get('categoryId'))
    Product.objects.create(
        name=body.get('name'),
        category=category,
        stock=body.get('stock'),
        stock_minimum=body.get('stockMinimum'),
        price=body.get('price')
    )
    payload['results']['message'] = 'Success create product'
    return JsonResponse(payload, safe=False, status=http.HTTPStatus.CREATED)


@csrf_exempt
@auth_with_token
@require_http_methods(["GET"])
def product_detail(request, pk):
    payload = {'results': {}, 'meta': {}, 'links': {'next': '', 'prev': ''}}
    product = Product.objects.get(pk=pk)
    payload['results'] = {
        'id': product.id,
        'category': {
            'id': product.category.id,
            'name': product.category.name
        },
        'name': product.name,
        'price': product.price,
        'stock': product.stock,
        'stock_minimum': product.stock_minimum
    }

    return JsonResponse(payload, safe=False, status=http.HTTPStatus.OK)


@csrf_exempt
@auth_with_token
@require_http_methods(["PUT"])
def product_edit(request, pk):
    payload = {'results': {}, 'meta': {}, 'links': {'next': '', 'prev': ''}}
    body = json.loads(request.body.decode('utf-8'))
    product = Product.objects.get(pk=pk)
    category = Category.objects.get(id=body.get('categoryId'))

    product.name = body.get('name')
    product.price = body.get('price')
    product.stock = body.get('stock')
    product.stock_minimum = body.get('stockMinimum')
    product.category = category
    product.save()

    payload['results']['message'] = 'Success update product'

    return JsonResponse(payload, safe=False, status=http.HTTPStatus.OK)

