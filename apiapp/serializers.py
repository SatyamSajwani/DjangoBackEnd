from rest_framework import serializers
from apiapp.models import *


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
    class Meta:
        model = TyrePattern
        fields = ['id', 'name', 'price', 'stock', 'image', 'brand']

class TyreSerializer(serializers.ModelSerializer):
    patterns = PatternSerializer(many=True, read_only=True)

    class Meta:
        model = TyreModel
        fields = ['id', 'width', 'ratio', 'rim', 'patterns']
        