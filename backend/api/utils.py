

from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import Favorite, Recipe, Shoppingcart

from .serializers import RecipeSerializer


class FavoriteShoppingcartMixin:
    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, **kwargs):
        try:
            recipe = get_object_or_404(Recipe, id=kwargs['pk'])
        except Http404:
            return Response({'errors': 'Рецепта не существует.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not Favorite.objects.filter(user=request.user,
                                       recipe=recipe).exists():
            if request.method == 'POST':
                serializer = RecipeSerializer(
                    recipe, data=request.data, context={"request": request})
                serializer.is_valid(raise_exception=True)
                favorite = Favorite(user=request.user, recipe=recipe)
                favorite.save()
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            get_object_or_404(Favorite, user=request.user,
                              recipe=recipe).delete()
            return Response(
                {'detail': 'Рецепт успешно удален из избранного.'},
                status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Рецепт уже в избранном.'},
            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,),
            pagination_class=None)
    def shopping_cart(self, request, **kwargs):
        try:
            recipe = get_object_or_404(Recipe, id=kwargs['pk'])
        except Http404:
            return Response({'errors': 'Рецепта не существует.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not Shoppingcart.objects.filter(user=request.user,
                                           recipe=recipe).exists():
            if request.method == 'POST':
                serializer = RecipeSerializer(recipe, data=request.data,
                                              context={"request": request})
                serializer.is_valid(raise_exception=True)
                shopping_cart = Shoppingcart(user=request.user, recipe=recipe)
                shopping_cart.save()
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            get_object_or_404(Shoppingcart, user=request.user,
                              recipe=recipe).delete()
            return Response(
                {'detail': 'Рецепт успешно удален из списка покупок.'},
                status=status.HTTP_204_NO_CONTENT
            )

        return Response({'errors': 'Рецепт уже в списке покупок.'},
                        status=status.HTTP_400_BAD_REQUEST)
