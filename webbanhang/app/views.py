from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from .models import *
import json
import datetime # Để xử lý ngày giờ khi thanh toán
from django.core.paginator import Paginator #  Để phân trang sản phẩm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

# Create your views here.

def home(request):
    # 1. Xử lý giỏ hàng
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
        user_not_login = "hidden"
        user_login = "show"
    else:
        items = []
        order = {'get_cart_items': 0, 'get_cart_total': 0}
        cartItems = order['get_cart_items']
        user_not_login = "show"
        user_login = "hidden"

    categories = Category.objects.filter(is_sub=False)
    products_list = Product.objects.all()

    # 2. Xử lý Phân trang (8 sản phẩm/trang)
    paginator = Paginator(products_list, 8) 
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    # Tạo danh sách trang rút gọn (Ví dụ: 1 ... 4 5 6 ... 10)
    try:
        custom_range = products.paginator.get_elided_page_range(products.number, on_each_side=1, on_ends=1)
    except AttributeError:
       
        custom_range = products.paginator.page_range

    context = {
        'products': products, 
        'cartItems': cartItems, 
        'user_not_login': user_not_login, 
        'user_login': user_login, 
        'categories': categories,
        'custom_range': custom_range
    }
    return render(request, 'app/home.html', context)

def cart(request):
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
        user_not_login = "hidden"
        user_login = "show"
    else:
        items = []
        order = {'get_cart_items': 0, 'get_cart_total': 0}
        cartItems = order['get_cart_items']
        user_not_login = "show"
        user_login = "hidden"

    categories = Category.objects.filter(is_sub=False)
    context = {'items': items, 'order': order, 'cartItems': cartItems, 'user_not_login': user_not_login, 'user_login': user_login, 'categories': categories}
    return render(request, 'app/cart.html', context)

def checkout(request):
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
        user_not_login = "hidden"
        user_login = "show"
    else:
        items = []
        order = {'get_cart_items': 0, 'get_cart_total': 0}
        cartItems = order['get_cart_items']
        user_not_login = "show"
        user_login = "hidden"

    categories = Category.objects.filter(is_sub=False)
    context = {'items': items, 'order': order, 'cartItems': cartItems, 'user_not_login': user_not_login, 'user_login': user_login, 'categories': categories}
    return render(request, 'app/checkout.html', context)

def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    customer = request.user
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)
    
    if action == 'add':
        orderItem.quantity += 1
    elif action == 'remove':
        orderItem.quantity -= 1
    
    orderItem.save()
    
    if orderItem.quantity <= 0:
        orderItem.delete()
        
    return JsonResponse('added', safe=False)

def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        total = float(data['form']['total'])
        order.transaction_id = transaction_id

        if total == order.get_cart_total:
            order.complete = True
        order.save()

        if order.complete:
            ShippingAddress.objects.create(
                customer=customer,
                order=order,
                address=data['shipping']['address'],
                city=data['shipping']['city'],
                state=data['shipping']['state'],
                mobile=data['shipping']['mobile'],
            )
    else:
        print('User is not logged in')

    return JsonResponse('Payment submitted..', safe=False)

def detail(request):
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
        user_not_login = "hidden"
        user_login = "show"
    else:
        items = []
        order = {'get_cart_items': 0, 'get_cart_total': 0}
        cartItems = order['get_cart_items']
        user_not_login = "show"
        user_login = "hidden"
    id = request.GET.get('id', '')
    products = Product.objects.filter(id=id)
    categories = Category.objects.filter(is_sub=False)
    context = {'items': items, 'order': order, 'cartItems': cartItems, 'user_not_login': user_not_login, 'user_login': user_login, 'categories': categories, 'products': products}
    return render(request, 'app/detail.html', context)

def category(request):
    if request.user.is_authenticated:
        user_not_login = "hidden"
        user_login = "show"
    else:
        user_not_login = "show"
        user_login = "hidden"
    categories = Category.objects.filter(is_sub=False)
    active_category = request.GET.get('category', '')
    if active_category:
        products = Product.objects.filter(category__slug=active_category)
    else:
        products = Product.objects.all() # Nếu không chọn danh mục thì hiện tất cả

    context = {'categories': categories, 'products': products, 'active_category': active_category, 'user_not_login': user_not_login, 'user_login': user_login}
    return render(request, 'app/category.html', context)

def search(request):
    searched = ""
    keys = [] 
    
    if request.method == "POST":
        searched = request.POST["searched"]
        keys = Product.objects.filter(name__contains=searched)
    
    if request.user.is_authenticated:
        customer = request.user
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
        user_not_login = "hidden"
        user_login = "show"
    else:
        items = []
        order = {'get_cart_items': 0, 'get_cart_total': 0}
        cartItems = order['get_cart_items']
        user_not_login = "show"
        user_login = "hidden"
        
    categories = Category.objects.filter(is_sub=False)
    products = Product.objects.all()
    
    context = {
        "searched": searched, 
        "keys": keys, 
        'products': products, 
        'cartItems': cartItems, 
        'user_not_login': user_not_login, 
        'user_login': user_login, 
        'categories': categories
    }
    return render(request, 'app/search.html', context)

def register(request):
    form = CreateUserForm()
    categories = Category.objects.filter(is_sub=False)
    user_not_login = "show"
    user_login = "hidden"

    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đăng ký thành công! Hãy đăng nhập.')
            return redirect('login')
        else:
            messages.error(request, 'Đăng ký thất bại! Vui lòng kiểm tra lại thông tin.')

    context = {'form': form, 'user_not_login': user_not_login, 'user_login': user_login, 'categories': categories}
    return render(request, 'app/register.html', context)

def loginPage(request):
    user_not_login = "show"
    user_login = "hidden"
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.info(request, 'Tên đăng nhập hoặc mật khẩu không đúng!')
            
    categories = Category.objects.filter(is_sub=False)
    context = {'user_not_login': user_not_login, 'user_login': user_login, 'categories': categories}
    return render(request, 'app/login.html', context)

def logoutPage(request):
    logout(request)
    return redirect('login')