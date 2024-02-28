from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import exceptions, serializers

from foodgram.constants import INVALID_USERNAMES
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscribe, User

from .fields import Base64ImageField


class IsSubscribedMixin:
    def get_is_subscribed(self, obj):
        request = self.context.get('request')

        if request and not request.user.is_anonymous:
            return Subscribe.objects.filter(user=request.user,
                                            author=obj).exists()
        return False


class UserReadSerializer(IsSubscribedMixin, UserSerializer):
    """Cписок пользователей."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'is_subscribed')


class UserCreateSerializer(UserCreateSerializer):
    """Создание нового пользователя."""
    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'password')
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
            'email': {'required': True, 'allow_blank': False},
        }

    def validate(self, obj):
        if obj.get('username') in INVALID_USERNAMES:
            raise serializers.ValidationError(
                {'username': 'Нельзя использовать этот username.'}
            )
        return obj


class RecipeSerializer(serializers.ModelSerializer):
    """Список рецептов."""
    image = Base64ImageField(read_only=True)
    name = serializers.ReadOnlyField()
    cooking_time = serializers.ReadOnlyField()
    user = UserSerializer

    class Meta:
        model = Recipe
        fields = ('id', 'name',
                  'image', 'cooking_time')

    def create(self, validated_data):
        return Recipe.objects.create(**validated_data)


class FavoriteShoppingCartBaseSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        return super().create(validated_data)

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeSerializer(
            instance.recipe, context={'request': request}
        ).data


class ShoppingCartSerializer(FavoriteShoppingCartBaseSerializer):
    class Meta:
        model = ShoppingCart
        fields = '__all__'


class FavoriteSerializer(FavoriteShoppingCartBaseSerializer):
    class Meta:
        model = Favorite
        fields = '__all__'


class BaseSubscriptionSerializer(IsSubscribedMixin,
                                 serializers.ModelSerializer):
    """Базовый сериализатор для работы с подписками пользователей."""
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        recipes_limit = request.GET.get('recipes_limit')

        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeSerializer(
            recipes, many=True,
            context={'request': request}).data


class SubscriptionsSerializer(BaseSubscriptionSerializer):
    """Авторы на которых подписан пользователь."""

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name',
                  'last_name', 'email', 'is_subscribed',
                  'recipes', 'recipes_count')


class SubscribeAuthorSerializer(BaseSubscriptionSerializer):
    """Подписка и отписка на автора."""
    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name',
                  'last_name', 'email', 'is_subscribed',
                  'recipes', 'recipes_count')


class SubscribeAuthorUserSerializer(BaseSubscriptionSerializer):
    class Meta:
        model = Subscribe
        fields = ('user', 'author')

    def validate(self, data):
        request = self.context.get('request')
        author = data.get('author')

        if request.user == author:
            raise exceptions.ValidationError(
                'Нельзя подписаться на самого себя!')

        if Subscribe.objects.filter(user=request.user, author=author).exists():
            raise exceptions.ValidationError(
                'Вы уже подписаны на этого автора.')
        return data

    def create(self, validated_data):
        return Subscribe.objects.create(**validated_data)

    def to_representation(self, instance):
        request = self.context.get('request')
        return SubscribeAuthorSerializer(
            instance.author, context={'request': request}
        ).data


class IngredientSerializer(serializers.ModelSerializer):
    """Ингредиенты."""
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """Теги."""
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Ингредиенты с количеством для рецепта."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name',
                  'measurement_unit', 'amount')


class ReadRecipeSerializer(serializers.ModelSerializer):
    """Рецепты."""
    author = UserReadSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, read_only=True, source='recipes')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags',
                  'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image',
                  'text', 'cooking_time')

    def get_is_favorited(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and Favorite.objects.filter(
                user=self.context['request'].user, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and ShoppingCart.objects.filter(
                user=self.context['request'].user,
                recipe=obj).exists()
        )


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Ингредиент и количество для создания рецепта."""
    id = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class CreateRecipeSerializer(serializers.ModelSerializer):
    """Создание, изменение и удаление рецепта."""
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(),
        error_messages={
            'does_not_exist': 'Указанного тега не существует'
        }
    )
    author = UserReadSerializer(read_only=True)
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients',
                  'tags', 'image',
                  'name', 'text',
                  'cooking_time', 'author')

    def validate_tags(self, tags):
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise serializers.ValidationError(
                    'Теги должны быть уникальными')
            tags_list.append(tag)
        return tags

    def validate(self, obj):
        if not obj.get('tags'):
            raise serializers.ValidationError(
                'Нужно указать минимум один тег.')
        if not obj.get('ingredients'):
            raise serializers.ValidationError(
                'Нужно указать минимум один ингредиент.')
        ingredient_id_list = [item['id'] for item in obj.get('ingredients')]
        unique_ingredient_id_list = set(ingredient_id_list)
        if len(ingredient_id_list) != len(unique_ingredient_id_list):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальными.')
        existing_ingredient_ids = Ingredient.objects.filter(
            id__in=ingredient_id_list).values_list('id', flat=True)
        if set(ingredient_id_list) != set(existing_ingredient_ids):
            raise serializers.ValidationError(
                'Указан несуществующий ингредиент.')
        return obj

    @transaction.atomic
    def tags_and_ingredients(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data)
        self.tags_and_ingredients(recipe, tags, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):

        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        RecipeIngredient.objects.filter(
            recipe=instance).delete()
        super().update(instance, validated_data)
        self.tags_and_ingredients(
            instance, tags, ingredients
        )
        return instance

    def to_representation(self, instance):
        return ReadRecipeSerializer(instance,
                                    context=self.context).data
