from rest_framework import serializers
from .models import Salary
from personnel.models import Personnel
from .calculations import calculate_gross_salary, calculate_net_salary
from decimal import Decimal




class PersonnelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Personnel
        fields = ['number_of_personnel','firstname', 'lastname']




class SalarySerializer(serializers.ModelSerializer):
    
    personnel = serializers.PrimaryKeyRelatedField(queryset=Personnel.objects.all(), write_only=True) 
    personnel_detail = PersonnelSerializer(source='personnel', read_only=True)

    gross_salary = serializers.SerializerMethodField(read_only=True)
    net_salary = serializers.SerializerMethodField(read_only=True)

    class Meta:
        
        
        model = Salary
        fields = ['user_id',
                  'personnel',
                  'personnel_detail',
                  'base_salary',
                  'housing_allowance',
                  'child_allowance',
                  'food_allowance',
                  'salary_start_date',
                  'gross_salary',
                  "net_salary",
                  'created_at',
                  'update_at'
                  ]
        
        read_only_fields = ['number_of_personnel', 'created_at', 'update_at', 'user_id']

        

    def get_gross_salary(self, obj: Salary) -> Decimal:
        return calculate_gross_salary(
            obj.base_salary, 
            obj.housing_allowance, 
            obj.child_allowance, 
            obj.food_allowance,
            obj.personnel.number_of_child,
            obj.personnel.marital_status.lower()
        )
    
    def get_net_salary(self, obj: Salary) -> Decimal:
        gross = self.get_gross_salary(obj)
        return calculate_net_salary(gross)
        
    def validate(self, data):
        personnel=data.get('personnel')
        child_allowance=data.get('child_allowance')

        if personnel.marital_status == 'single' or (personnel.marital_status == 'married' and personnel.number_of_child in [0, None]):

            if child_allowance not in [0, None]:

                raise serializers.ValidationError("Personnel with no children or single cannot have a child allowance.")
            

        if self.instance:
            if self.instance.personnel == personnel:
                return data

        if Salary.objects.filter(personnel=personnel).exists():
            raise serializers.ValidationError(f'A salary record for personnel {personnel} already exists.')

        return data
        