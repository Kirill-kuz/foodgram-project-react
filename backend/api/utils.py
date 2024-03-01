from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from recipes.models import Recipe


class FavoriteShoppingCartMixin:
    def process_request(self, request, kwargs, model,
                        action_type, serializer_class, message):
        try:
            recipe = get_object_or_404(Recipe, id=kwargs['pk'])
        except Http404:
            return Response({'errors': 'Рецепта не существует.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'POST':
            if not model.objects.filter(user=request.user,
                                        recipe=recipe).exists():
                serializer_data = {'user': request.user.id,
                                   'recipe': recipe.id}
                serializer = serializer_class(
                    data=serializer_data, context={'request': request})
                serializer.is_valid(raise_exception=True)
                serializer.save(user=request.user, recipe=recipe)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)
            return Response({'errors': f"Рецепт уже в {message}"},
                            status=status.HTTP_400_BAD_REQUEST)

        get_object_or_404(model, user=request.user, recipe=recipe).delete()
        return Response({'detail': message}, status=status.HTTP_204_NO_CONTENT)
