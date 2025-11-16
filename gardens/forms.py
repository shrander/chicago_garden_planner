from django import forms
from .models import Garden, Plant, PlantingNote


class GardenForm(forms.ModelForm):
    """Form for creating and editing gardens"""

    class Meta:
        model = Garden
        fields = ['name', 'description', 'size', 'width', 'height', 'is_public']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., My Backyard Garden',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe your garden layout and goals...',
            }),
            'size': forms.Select(attrs={
                'class': 'form-select',
            }),
            'width': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 50,
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 50,
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        help_texts = {
            'width': 'Width in feet (1-50)',
            'height': 'Height in feet (1-50)',
            'is_public': 'Allow other users to view this garden',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default layout data on new gardens
        if not self.instance.pk:
            self.fields['size'].initial = '10x10'

    def clean(self):
        cleaned_data = super().clean()
        size = cleaned_data.get('size')
        width = cleaned_data.get('width')
        height = cleaned_data.get('height')

        # Auto-set width and height for non-custom sizes
        if size and size != 'custom':
            try:
                h, w = size.split('x')
                cleaned_data['width'] = int(w)
                cleaned_data['height'] = int(h)
            except ValueError:
                pass

        # Validate custom size dimensions
        if size == 'custom':
            if not width or not height:
                raise forms.ValidationError('Custom gardens must have both width and height specified.')
            if width < 1 or width > 50:
                raise forms.ValidationError('Width must be between 1 and 50 feet.')
            if height < 1 or height > 50:
                raise forms.ValidationError('Height must be between 1 and 50 feet.')

        return cleaned_data

    def save(self, commit=True):
        garden = super().save(commit=False)

        # Initialize empty grid layout if new garden
        if not garden.pk or not garden.layout_data:
            # Create empty grid based on dimensions
            width = garden.width
            height = garden.height
            empty_grid = [['empty space' for _ in range(width)] for _ in range(height)]
            garden.layout_data = {'grid': empty_grid}

        if commit:
            garden.save()

        return garden


class PlantForm(forms.ModelForm):
    """Form for creating and editing custom plants"""

    planting_seasons = forms.MultipleChoiceField(
        choices=Plant.SEASONS,
        widget=forms.CheckboxSelectMultiple,
        help_text='Select all seasons when this plant can be planted'
    )

    class Meta:
        model = Plant
        fields = [
            'name', 'latin_name', 'symbol', 'color', 'plant_type', 'life_cycle',
            'planting_seasons', 'days_to_harvest', 'spacing_inches',
            'weeks_before_last_frost_start', 'weeks_after_last_frost_transplant',
            'direct_sow', 'days_to_germination', 'days_before_transplant_ready', 'transplant_to_harvest_days',
            'chicago_notes', 'yield_per_plant', 'pest_deterrent_for', 'companion_plants'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'latin_name': forms.TextInput(attrs={'class': 'form-control'}),
            'symbol': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'plant_type': forms.Select(attrs={'class': 'form-select'}),
            'life_cycle': forms.Select(attrs={'class': 'form-select'}),
            'days_to_harvest': forms.NumberInput(attrs={'class': 'form-control'}),
            'spacing_inches': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'weeks_before_last_frost_start': forms.NumberInput(attrs={'class': 'form-control'}),
            'weeks_after_last_frost_transplant': forms.NumberInput(attrs={'class': 'form-control'}),
            'direct_sow': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'days_to_germination': forms.NumberInput(attrs={'class': 'form-control'}),
            'days_before_transplant_ready': forms.NumberInput(attrs={'class': 'form-control'}),
            'transplant_to_harvest_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'yield_per_plant': forms.TextInput(attrs={'class': 'form-control'}),
            'chicago_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'pest_deterrent_for': forms.TextInput(attrs={'class': 'form-control'}),
            'companion_plants': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 6}),
        }


class PlantingNoteForm(forms.ModelForm):
    """Form for creating garden notes"""

    class Meta:
        model = PlantingNote
        fields = ['plant', 'title', 'note_text', 'grid_position']
        widgets = {
            'plant': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'note_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'grid_position': forms.TextInput(attrs={'class': 'form-control'}),
        }
