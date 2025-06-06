from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from rest_framework import exceptions, filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from foodgram.constants import NAME_DOWNLOAD_FILE
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscribe, User
from .filters import RecipeFilter
from .pagination import CustomPaginator
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    CreateRecipeSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    ReadRecipeSerializer,
    ShoppingCartSerializer,
    SubscribeAuthorUserSerializer,
    SubscriptionsSerializer,
    TagSerializer,
    UserCreateSerializer,
    UserReadSerializer,
)
from .utils import FavoriteShoppingCartMixin


class UserViewSet(mixins.CreateModelMixin,
                  mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = CustomPaginator

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserReadSerializer
        return UserCreateSerializer

    @action(detail=False, methods=['get'],
            pagination_class=None,
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        serializer = UserReadSerializer(request.user)
        return Response(serializer.data,
                        status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'],
            permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        current_password = serializer.validated_data.get('current_password')
        new_password = serializer.validated_data.get('new_password')

        if not self.request.user.check_password(current_password):
            raise ValidationError(
                {'detail': 'Пароли не совпадают.'},
                code=status.HTTP_400_BAD_REQUEST)

        self.request.user.set_password(new_password)
        self.request.user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['GET'],
            permission_classes=(IsAuthenticated,),
            pagination_class=CustomPaginator)
    def subscriptions(self, request):
        queryset = User.objects.filter(subscribing__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(page, many=True,
                                             context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, **kwargs):
        author = get_object_or_404(User, id=kwargs['pk'])

        if request.method == 'POST':
            serializer = SubscribeAuthorUserSerializer(
                data={'user': request.user.id, 'author': author.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if not Subscribe.objects.filter(user=request.user,
                                        author=author).exists():
            raise exceptions.ValidationError(
                'Подписка не оформлена, либо удалена.')
        get_object_or_404(Subscribe,
                          user=request.user, author=author).delete()
        return Response(
            {'detail': 'Успешная отписка'},
            status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny, )
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (filters.SearchFilter, )
    search_fields = ('^name', )


class TagViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    permission_classes = (AllowAny, )
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(FavoriteShoppingCartMixin, viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPaginator
    permission_classes = (IsAuthorOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'create', 'delete']

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, **kwargs):
        action_type = 'избранное'
        serializer_class = FavoriteSerializer
        return self.process_request(request, kwargs, Favorite,
                                    action_type, serializer_class, action_type)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,), pagination_class=None)
    def shopping_cart(self, request, **kwargs):
        action_type = 'списке покупок'
        serializer_class = ShoppingCartSerializer
        return self.process_request(request, kwargs, ShoppingCart,
                                    action_type, serializer_class, action_type)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ReadRecipeSerializer
        return CreateRecipeSerializer

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request, **kwargs):
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__shopping_recipe__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
        )
        max_length = max(
            len(ingredient["ingredient__name"]) for ingredient in ingredients)
        file_list = [
            f'{ingredient["ingredient__name"].ljust(max_length, ".")} '
            f'{ingredient["total_amount"]} '
            f'{ingredient["ingredient__measurement_unit"]}.'
            for ingredient in ingredients
        ]
        file_content = 'Список покупок:\n' + '\n'.join(file_list)
        file = HttpResponse(file_content, content_type='text/plain')
        file['Content-Disposition'] = (
            f'attachment; filename={NAME_DOWNLOAD_FILE}')
        return file
