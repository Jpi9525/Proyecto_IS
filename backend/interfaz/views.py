from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
import json

def seleccionar_generos(request):
    """Vista principal para mostrar el formulario de selección de géneros"""
    # Lista de géneros con imágenes
    generos = [
        {'nombre': 'Rock', 'valor': 'Rock', 'imagen': 'https://images.unsplash.com/photo-1498038432885-c6f3f1b912ee?w=300&h=300&fit=crop'},
        {'nombre': 'Pop', 'valor': 'Pop', 'imagen': 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=300&h=300&fit=crop'},
        {'nombre': 'Jazz', 'valor': 'Jazz', 'imagen': 'https://images.unsplash.com/photo-1415201364774-f6f0bb35f28f?w=300&h=300&fit=crop'},
        {'nombre': 'Hip-hop', 'valor': 'Hip-hop', 'imagen': 'https://images.unsplash.com/photo-1571608971218-df35abe11326?w=300&h=300&fit=crop'},
        {'nombre': 'Electronic', 'valor': 'Electronic', 'imagen': 'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=300&h=300&fit=crop'},
        {'nombre': 'Classical', 'valor': 'Classical', 'imagen': 'https://images.unsplash.com/photo-1519683384663-1a0ec7d3e54a?w=300&h=300&fit=crop'},
        {'nombre': 'Reggae', 'valor': 'Reggae', 'imagen': 'https://images.unsplash.com/photo-1501612780327-45045538702b?w=300&h=300&fit=crop'},
        {'nombre': 'Metal', 'valor': 'Metal', 'imagen': 'https://images.unsplash.com/photo-1506091403742-e3aa39518db5?w=300&h=300&fit=crop'},
        {'nombre': 'Country', 'valor': 'Country', 'imagen': 'https://images.unsplash.com/photo-1516924962500-2b4b3b99ea02?w=300&h=300&fit=crop'},
        {'nombre': 'R&B', 'valor': 'R&B', 'imagen': 'https://images.unsplash.com/photo-1571330735066-03aaa9429d89?w=300&h=300&fit=crop'},
    ]
    
    context = {
        'generos': generos
    }
    return render(request, 'interfaz/seleccionar_generos.html', context)

def guardar_generos(request):
    """Vista para procesar los géneros seleccionados"""
    if request.method == 'POST':
        # Verificar si es petición AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                data = json.loads(request.body)
                generos_seleccionados = data.get('generos', [])
            except:
                generos_seleccionados = request.POST.getlist('generos')
        else:
            generos_seleccionados = request.POST.getlist('generos')
        
        # Validaciones
        if len(generos_seleccionados) != 3:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Debes seleccionar al menos un género'})
            messages.error(request, 'Debes seleccionar al menos un género')
            return redirect('home')
            
        elif len(generos_seleccionados) > 3:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Solo puedes seleccionar hasta 3 géneros'})
            messages.error(request, 'Solo puedes seleccionar hasta 3 géneros')
            return redirect('home')
        
        # Guardar en sesión
        request.session['generos_favoritos'] = generos_seleccionados
        
        # Debug
        print(f"✅ Géneros seleccionados: {generos_seleccionados}")
        
        # Respuesta AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Géneros guardados exitosamente',
                'generos': generos_seleccionados
            })
        
        messages.success(request, f'¡Excelente! Has seleccionado: {", ".join(generos_seleccionados)}')
        return redirect('home')
    
    return redirect('home')

