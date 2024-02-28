from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import Favorite, Recipe, ShoppingCart
from .serializers import ShoppingCartSerializer, FavoriteSerializer


class FavoriteShoppingCartMixin:
    def process_request(self, request, kwargs, model, message):
        try:
            recipe = get_object_or_404(Recipe, id=kwargs['pk'])
        except Http404:
            return Response({'errors': 'Рецепта не существует.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if not model.objects.filter(user=request.user, recipe=recipe).exists():
            serializer_data = {'user': request.user.id, 'recipe': recipe.id}
            if request.method == 'POST':
                if model == Favorite:
                    serializer = FavoriteSerializer(
                        data=serializer_data, context={'request': request})
                elif model == ShoppingCart:
                    serializer = ShoppingCartSerializer(
                        data=serializer_data, context={'request': request})
                serializer.is_valid(raise_exception=True)
                serializer.save(user=request.user, recipe=recipe)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)
            get_object_or_404(model, user=request.user, recipe=recipe).delete()
            return Response({'detail': message},
                            status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': f"Рецепт уже в {message}"},
            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, **kwargs):
        return self.process_request(request, kwargs, Favorite, 'избранном')

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,), pagination_class=None)
    def shopping_cart(self, request, **kwargs):
        return self.process_request(
            request, kwargs, ShoppingCart, 'списке покупок')
