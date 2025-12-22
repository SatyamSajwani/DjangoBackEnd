from rest_framework import serializers
from apiapp.models import *
from decimal import Decimal


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
    fields = '__all__'

class DistributorSerializer(serializers.ModelSerializer):
    
    brands=serializers.PrimaryKeyRelatedField(many=True,queryset=Brand.objects.all(), required=False)
    # distributor_id=serializers.ReadOnlyField()
    class Meta:
        model=CreateDistributor
        fields= '__all__'

class SubuserSerializer(serializers.ModelSerializer):
    distributor=serializers.PrimaryKeyRelatedField(queryset=CreateDistributor.objects.all(),)
    # subuser_id=serializers.ReadOnlyField()
    class Meta:
        model = CreateSubUser
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        subuser = CreateSubUser(**validated_data)
        if password:
            subuser.set_password(password)
        subuser.save()
        return subuser

    def update(self, instance, validated_data):
        # if password present, hash it
        raw_password = validated_data.pop('password', None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if raw_password:
            instance.set_password(raw_password)
        instance.save()
        return instance


class PatternSerializer(serializers.ModelSerializer):
    discounted_price = serializers.SerializerMethodField()
    class Meta:
        model = TyrePattern
        fields = ['id', 'name', 'price', 'discounted_price', 'stock', 'image', 'brand']

    def get_discounted_price(self, obj):
        request = self.context.get('request')

        # No request / token → show base price
        if not request or not hasattr(request, 'user'):
            return obj.price

        user = request.user
        discount = Decimal("0")

        # Subuser discount
        if isinstance(user, CreateSubUser):
            discount = Decimal(str(user.discount_percantage or 0))

        # Distributor (no discount)
        elif isinstance(user, CreateDistributor):
            discount = Decimal("0")

        price = Decimal(obj.price)
        final_price = price - (price * discount / Decimal("100"))
        return round(final_price, 2)


class TyreSerializer(serializers.ModelSerializer):
    patterns = serializers.SerializerMethodField()

    class Meta:
        model = TyreModel
        fields = ['id', 'width', 'ratio', 'rim', 'patterns']

    def get_patterns(self, obj):
        request = self.context.get('request')
        serializer = PatternSerializer(obj.patterns.all(), many=True, context={'request': request})
        return serializer.data