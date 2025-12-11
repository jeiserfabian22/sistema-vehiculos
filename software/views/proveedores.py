
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from software.models.ProveedoresModel import Proveedor
from software.models.Tipo_entidadModel import TipoEntidad
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos

# Importar la función de TokenPeru
from software.tokenperu_api import consultar_documento


def proveedores(request):
    """Vista principal que lista todos los proveedores activos"""
    id2 = request.session.get('idtipousuario')
    if id2:
        permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
        proveedores_registros = Proveedor.objects.filter(estado=1).select_related('id_tipo_entidad')
        tipos_entidad = TipoEntidad.objects.filter(estado=1)

        data = {
            'proveedores_registros': proveedores_registros,
            'tipos_entidad': tipos_entidad,
            'permisos': permisos
        }
        
        return render(request, 'proveedores/proveedores.html', data)
    else:
        return HttpResponse("<h1>No tiene acceso señor</h1>")


def eliminar_proveedor(request, id):
    """Eliminación lógica del proveedor (cambia estado a 0)"""
    Proveedor.objects.filter(idproveedor=id).update(estado=0)
    return redirect('proveedores')


def agregar_proveedor(request):
    """Agregar un nuevo proveedor"""
    try:
        numdoc = request.POST.get('numdocProveedor')
        razonsocial = request.POST.get('razonsocialProveedor')
        direccion = request.POST.get('direccionProveedor', '')
        telefono = request.POST.get('telefonoProveedor', '')
        email = request.POST.get('emailProveedor', '')
        nombre_comercial = request.POST.get('nombreComercialProveedor', '')
        departamento = request.POST.get('departamentoProveedor', '')
        provincia = request.POST.get('provinciaProveedor', '')
        distrito = request.POST.get('distritoProveedor', '')
        id_tipo_entidad = request.POST.get('tipoEntidadProveedor')

        proveedor = Proveedor.objects.create(
            numdoc=numdoc,
            razonsocial=razonsocial,
            direccion=direccion,
            telefono=telefono,
            email=email,
            nombre_comercial=nombre_comercial,
            departamento=departamento,
            provincia=provincia,
            distrito=distrito,
            id_tipo_entidad_id=id_tipo_entidad,
            estado=1
        )
        
        # Si es una petición AJAX (desde el módulo de compras)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'id': proveedor.idproveedor,
                'razonsocial': proveedor.razonsocial,
                'numdoc': proveedor.numdoc
            })
        
        # Si es petición normal (desde el módulo de proveedores)
        return redirect('proveedores')
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        return redirect('proveedores')


def editar_proveedor(request):
    """Editar un proveedor existente"""
    id = request.POST.get('idProveedor')
    numdoc = request.POST.get('numdocProveedor')
    razonsocial = request.POST.get('razonsocialProveedor')
    direccion = request.POST.get('direccionProveedor', '')
    telefono = request.POST.get('telefonoProveedor', '')
    email = request.POST.get('emailProveedor', '')
    nombre_comercial = request.POST.get('nombreComercialProveedor', '')
    departamento = request.POST.get('departamentoProveedor', '')
    provincia = request.POST.get('provinciaProveedor', '')
    distrito = request.POST.get('distritoProveedor', '')
    id_tipo_entidad = request.POST.get('tipoEntidadProveedor')

    proveedor = Proveedor.objects.get(idproveedor=id)
    proveedor.numdoc = numdoc
    proveedor.razonsocial = razonsocial
    proveedor.direccion = direccion
    proveedor.telefono = telefono
    proveedor.email = email
    proveedor.nombre_comercial = nombre_comercial
    proveedor.departamento = departamento
    proveedor.provincia = provincia
    proveedor.distrito = distrito
    proveedor.id_tipo_entidad_id = id_tipo_entidad
    proveedor.save()
    
    return redirect('proveedores')


# ==================== FUNCIÓN TOKENPERU ====================
@csrf_exempt
def autocompletar_proveedor(request):
    """Vista AJAX para autocompletar datos de proveedor desde APIs.net.pe"""
    numero = request.GET.get('numero', '')
    
    if not numero:
        return JsonResponse({
            'success': False,
            'error': 'Se requiere el número de documento'
        })
    
    try:
        # Consultar APIs.net.pe
        resultado = consultar_documento(numero)
        
        # Formatear respuesta según tipo de documento
        if resultado['tipo_documento'] == 'DNI':
            # Para DNI: Razón Social y Nombre Comercial son iguales
            nombre_completo = resultado.get('nombre_completo', '')
            
            response_data = {
                'success': True,
                'tipo': 'DNI',
                'id_tipo_entidad': 1,
                'numdoc': resultado.get('dni', numero),
                'razonsocial': nombre_completo,
                'nombre_comercial': nombre_completo,
                'direccion': resultado.get('direccion', ''),
                'telefono': '',
                'email': '',
                'departamento': '',
                'provincia': '',
                'distrito': ''
            }
        else:  # RUC
            # Para RUC: Razón Social y Nombre Comercial son diferentes
            response_data = {
                'success': True,
                'tipo': 'RUC',
                'id_tipo_entidad': 6,
                'numdoc': resultado.get('ruc', numero),
                'razonsocial': resultado.get('razon_social', ''),
                'nombre_comercial': resultado.get('nombre_comercial', ''),
                'direccion': resultado.get('direccion', ''),
                'departamento': resultado.get('departamento', ''),
                'provincia': resultado.get('provincia', ''),
                'distrito': resultado.get('distrito', ''),
                'ubigeo': resultado.get('ubigeo', ''),
                'estado': resultado.get('estado', ''),
                'condicion': resultado.get('condicion', ''),
                'telefono': '',
                'email': ''
            }
        
        return JsonResponse(response_data)
        
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error: {str(e)}'})
    

def obtener_ultimo_proveedor(request):
    """Obtiene el último proveedor registrado para selección automática"""
    try:
        ultimo_proveedor = Proveedor.objects.filter(estado=1).order_by('-idproveedor').first()
        
        if ultimo_proveedor:
            return JsonResponse({
                'success': True,
                'id': ultimo_proveedor.idproveedor,
                'razonsocial': ultimo_proveedor.razonsocial,
                'numdoc': ultimo_proveedor.numdoc
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No se encontró el proveedor'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


