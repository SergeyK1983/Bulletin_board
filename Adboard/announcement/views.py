from django.shortcuts import redirect
from rest_framework.exceptions import APIException
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework import generics, permissions, status
from django_filters.rest_framework import DjangoFilterBackend

from cabinet.models import User
from .filters import BoardListFilter
from .forms import FormPost
from .models import Post
from .pagination import BoardListPagination
from .serializer import BoardSerializer, BoardPageSerializer
from .services import correct_form_category_for_serializer


class BoardListView(generics.ListAPIView):
    """ Вывод карточек всех объявлений на странице """

    serializer_class = BoardSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Post.objects.filter().all().order_by('-date_create')
    pagination_class = BoardListPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = BoardListFilter
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = "announcement/board_title.html"

    def get(self, request, *args, **kwargs):
        # все танцы с фильтрацией из-за пагинации в основном для TemplateHTMLRenderer, а так могло бы работать штатно.
        queryset = self.get_queryset()
        filter_board = self.filterset_class(self.request.GET, queryset)
        qs = filter_board.qs
        # print(len(qs))  ели пагинация будет глючить, использовать для подсчета страничек
        pages = self.paginate_queryset(queryset=qs)

        if request.headers.get('Content-Type') == 'application/json':
            if pages is not None:
                serializer = self.get_serializer(pages, many=True)
                return self.get_paginated_response(serializer.data)
            else:
                return self.list(request, *args, **kwargs)
        else:
            if pages is not None:
                return self.get_paginated_response(pages)
            else:
                return Response({"board_list": qs, "pagination": False})


class BoardPageListView(generics.ListAPIView):
    """ Вывод страницы с объявлением """

    serializer_class = BoardSerializer
    permission_classes = [permissions.AllowAny]
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = "announcement/board_page.html"

    def get_queryset(self):
        queryset = Post.objects.filter(id=self.kwargs['pk'])  # может вернуть пустой queryset
        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not list(queryset):
            data = {'error': 'Такой страницы нет либо записей нет.',
                    'status': 'HTTP_404_NOT_FOUND'}
            if request.headers.get('Content-Type') == 'application/json':
                return Response(data, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({'error': data}, template_name='announcement/page_error.html')

        if request.headers.get('Content-Type') == 'application/json':
            return self.list(request, *args, **kwargs)
        else:
            return Response({'board_page': queryset})


class PageCreateView(generics.CreateAPIView):
    """ Создание нового объявления """

    serializer_class = BoardPageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)  # без этого с формы ничего не получить
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = "announcement/create_page.html"

    def get(self, request, *args, **kwargs):
        # метод get из-за TemplateHTMLRenderer
        user = User.objects.filter(username=request.user.username)
        form = FormPost()
        return Response({"profile": user, "form": form})  # "serializer": self.get_serializer() трудно настроить стили

    def post(self, request, *args, **kwargs):
        data = correct_form_category_for_serializer(request=request)
        # Контекст нужно передать, т.к. в сериалайзере используется поле с контекстом из request
        serializer = BoardPageSerializer(data=data, context={'request': request})

        if not serializer.is_valid():
            data = {'error': 'Переданные данные не корректны ...', 'status': 'HTTP_400_BAD_REQUEST'}
            if request.headers.get('Content-Type') == 'application/json':
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': data}, template_name='announcement/page_error.html')

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
                if request.headers.get('Content-Type') == 'application/json':
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                return redirect('board_list')
            except APIException:
                data = {'error': 'Сервер не отвечает.', 'status': 'HTTP_500_INTERNAL_SERVER_ERROR'}
                if request.headers.get('Content-Type') == 'application/json':
                    return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                return Response({'error': data}, template_name='announcement/page_error.html')


class PageUpdateView(generics.RetrieveUpdateAPIView):
    """ Контроллер изменения объявления """

    serializer_class = BoardPageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = "announcement/update_page_form.html"

    def get_queryset(self):
        queryset = Post.objects.filter(id=self.kwargs['pk'])
        return queryset

    def get(self, request, *args, **kwargs):
        # метод get из-за TemplateHTMLRenderer
        user = User.objects.filter(username=request.user.username)
        queryset = self.get_queryset()
        initial = {
            "category": queryset[0].category,
            "title": queryset[0].title,
            "article": queryset[0].article,
        }
        form = FormPost(initial=initial)  # instance=queryset[0] все поля или initial переопределить поля
        return Response({"profile": user, "posts": queryset, "form": form})

    def post(self, request, *args, **kwargs):
        data = correct_form_category_for_serializer(request=request)
        instance = get_object_or_404(Post, pk=kwargs['pk'])  # можно еще так self.get_object()
        serializer = BoardPageSerializer(instance=instance, data=data, context={'request': request})

        if not serializer.is_valid():
            data = {'error': 'Что-то пошло не так ...', 'status': 'HTTP_400_BAD_REQUEST'}
            if request.headers.get('Content-Type') == 'application/json':
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': data}, template_name='announcement/page_error.html')

        if serializer.is_valid():
            try:
                # Если в .save() добавить owner=other/dict/, то добавит в validated_data и можно будет пользовать
                serializer.save()
                if request.headers.get('Content-Type') == 'application/json':
                    data = {'state': 1, 'message': 'Изменение прошло успешно'}
                    return Response(data, status=status.HTTP_200_OK)
                return redirect('board_list')
            except APIException:
                data = {'error': 'Сервер не отвечает.', 'status': 'HTTP_500_INTERNAL_SERVER_ERROR'}
                if request.headers.get('Content-Type') == 'application/json':
                    return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                return Response({'error': data}, template_name='announcement/page_error.html')


class PageDestroyView(generics.DestroyAPIView):
    """ Удаление объявления """

    serializer_class = BoardPageSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Post.objects.all()

