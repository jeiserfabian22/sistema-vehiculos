from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from software.models.ClienteModel import Cliente
from software.models.Tipo_entidadModel import TipoEntidad
from software.models.detalletipousuarioxmodulosModel import Detalletipousuarioxmodulos

# Importar la función de TokenPeru
from software.tokenperu_api import consultar_documento


def clientes(request):
    """Vista principal que lista todos los clientes activos"""
    id2 = request.session.get('idtipousuario')
    if id2:
        permisos = Detalletipousuarioxmodulos.objects.filter(idtipousuario=id2)
        clientes_registros = Cliente.objects.filter(estado=1).select_related('id_tipo_entidad')
        tipos_entidad = TipoEntidad.objects.filter(estado=1)

        data = {
            'clientes_registros': clientes_registros,
            'tipos_entidad': tipos_entidad,
            'permisos': permisos
        }
        
        return render(request, 'clientes/clientes.html', data)
    else:
        return HttpResponse("<h1>No tiene acceso señor</h1>")


def eliminar_cliente(request, id):
    """Eliminación lógica del cliente (cambia estado a 0)"""
    Cliente.objects.filter(idcliente=id).update(estado=0)
    return redirect('clientes')


def agregar_cliente(request):
    """Agregar un nuevo cliente con validaciones - Compatible con AJAX"""
    try:
        numdoc = request.POST.get('numdocCliente', '').strip()
        razonsocial = request.POST.get('razonsocialCliente', '').strip()
        direccion = request.POST.get('direccionCliente', '').strip()
        telefono = request.POST.get('telefonoCliente', '').strip()
        nombre_comercial = request.POST.get('nombreComercialCliente', '').strip()
        id_tipo_entidad = request.POST.get('tipoEntidadCliente', '').strip()

        # ========== VALIDACIONES ==========
        
        # 1. Validar tipo de entidad
        if not id_tipo_entidad or id_tipo_entidad == '':
            error_msg = "Debe seleccionar un tipo de entidad"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        try:
            tipo_entidad = TipoEntidad.objects.get(id_tipo_entidad=id_tipo_entidad, estado=1)
        except TipoEntidad.DoesNotExist:
            error_msg = "El tipo de entidad seleccionado no existe"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        # 2. Validar número de documento
        if not numdoc or numdoc == '':
            error_msg = "El número de documento es obligatorio"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        if not numdoc.isdigit():
            error_msg = "El número de documento debe contener solo números"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        if len(numdoc) < 8 or len(numdoc) > 11:
            error_msg = "El número de documento debe tener entre 8 y 11 dígitos"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        # 3. Validar que el documento no esté duplicado
        if Cliente.objects.filter(numdoc=numdoc, estado=1).exists():
            error_msg = f"Ya existe un cliente con el documento {numdoc}"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        # 4. Validar razón social
        if not razonsocial or razonsocial == '':
            error_msg = "La razón social / nombre completo es obligatorio"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        if len(razonsocial) < 3:
            error_msg = "La razón social debe tener al menos 3 caracteres"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        # 5. Validar teléfono (si se proporciona)
        if telefono and not telefono.isdigit():
            error_msg = "El teléfono debe contener solo números"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        if telefono and (len(telefono) < 7 or len(telefono) > 15):
            error_msg = "El teléfono debe tener entre 7 y 15 dígitos"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        # 6. Validar longitudes máximas
        if len(razonsocial) > 255:
            error_msg = "La razón social no puede exceder 255 caracteres"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        if nombre_comercial and len(nombre_comercial) > 255:
            error_msg = "El nombre comercial no puede exceder 255 caracteres"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        if direccion and len(direccion) > 255:
            error_msg = "La dirección no puede exceder 255 caracteres"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error_msg}, status=400)
            return HttpResponse(error_msg, status=400)
        
        # ========== CREAR CLIENTE ==========
        cliente = Cliente.objects.create(
            numdoc=numdoc,
            razonsocial=razonsocial,
            direccion=direccion if direccion else '',
            telefono=telefono if telefono else '',
            nombre_comercial_cliente=nombre_comercial if nombre_comercial else '',
            id_tipo_entidad=tipo_entidad,
            estado=1
        )
        
        # ✅ DETECTAR SI ES AJAX (desde modal de ventas)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'ok': True,
                'idcliente': cliente.idcliente,
                'numdoc': cliente.numdoc,
                'razonsocial': cliente.razonsocial,
                'nombre_comercial': cliente.nombre_comercial_cliente or '',
                'direccion': cliente.direccion or '',
                'telefono': cliente.telefono or '',
                'tipo_documento': cliente.tipo_documento
            })
        
        # Si NO es AJAX, redireccionar normalmente
        return redirect('clientes')
        
    except Exception as e:
        error_msg = f"Error al guardar el cliente: {str(e)}"
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': error_msg}, status=500)
        return HttpResponse(error_msg, status=500)


def editar_cliente(request):
    """Editar un cliente existente con validaciones"""
    try:
        id = request.POST.get('idCliente', '').strip()
        numdoc = request.POST.get('numdocCliente', '').strip()
        razonsocial = request.POST.get('razonsocialCliente', '').strip()
        direccion = request.POST.get('direccionCliente', '').strip()
        telefono = request.POST.get('telefonoCliente', '').strip()
        nombre_comercial = request.POST.get('nombreComercialCliente', '').strip()
        id_tipo_entidad = request.POST.get('tipoEntidadCliente', '').strip()

        # ========== VALIDACIONES ==========
        
        # 1. Validar ID del cliente
        if not id or id == '':
            return HttpResponse("ID de cliente inválido", status=400)
        
        try:
            cliente = Cliente.objects.get(idcliente=id)
        except Cliente.DoesNotExist:
            return HttpResponse("El cliente no existe", status=400)
        
        # 2. Validar tipo de entidad
        if not id_tipo_entidad or id_tipo_entidad == '':
            return HttpResponse("Debe seleccionar un tipo de entidad", status=400)
        
        try:
            tipo_entidad = TipoEntidad.objects.get(id_tipo_entidad=id_tipo_entidad, estado=1)
        except TipoEntidad.DoesNotExist:
            return HttpResponse("El tipo de entidad seleccionado no existe", status=400)
        
        # 3. Validar número de documento
        if not numdoc or numdoc == '':
            return HttpResponse("El número de documento es obligatorio", status=400)
        
        if not numdoc.isdigit():
            return HttpResponse("El número de documento debe contener solo números", status=400)
        
        if len(numdoc) < 8 or len(numdoc) > 11:
            return HttpResponse("El número de documento debe tener entre 8 y 11 dígitos", status=400)
        
        # 4. Validar que el documento no esté duplicado (excepto el cliente actual)
        if Cliente.objects.filter(numdoc=numdoc, estado=1).exclude(idcliente=id).exists():
            return HttpResponse(f"Ya existe otro cliente con el documento {numdoc}", status=400)
        
        # 5. Validar razón social
        if not razonsocial or razonsocial == '':
            return HttpResponse("La razón social / nombre completo es obligatorio", status=400)
        
        if len(razonsocial) < 3:
            return HttpResponse("La razón social debe tener al menos 3 caracteres", status=400)
        
        # 6. Validar teléfono (si se proporciona)
        if telefono and not telefono.isdigit():
            return HttpResponse("El teléfono debe contener solo números", status=400)
        
        if telefono and (len(telefono) < 7 or len(telefono) > 15):
            return HttpResponse("El teléfono debe tener entre 7 y 15 dígitos", status=400)
        
        # 7. Validar longitudes máximas
        if len(razonsocial) > 255:
            return HttpResponse("La razón social no puede exceder 255 caracteres", status=400)
        
        if nombre_comercial and len(nombre_comercial) > 255:
            return HttpResponse("El nombre comercial no puede exceder 255 caracteres", status=400)
        
        if direccion and len(direccion) > 255:
            return HttpResponse("La dirección no puede exceder 255 caracteres", status=400)
        
        # ========== ACTUALIZAR CLIENTE ==========
        cliente.numdoc = numdoc
        cliente.razonsocial = razonsocial
        cliente.direccion = direccion if direccion else ''
        cliente.telefono = telefono if telefono else ''
        cliente.nombre_comercial_cliente = nombre_comercial if nombre_comercial else ''
        
        # ✅ CORRECCIÓN: Usar _id para asignar la Foreign Key
        cliente.id_tipo_entidad_id = id_tipo_entidad
        
        cliente.save()
        
        return redirect('clientes')
        
    except Exception as e:
        return HttpResponse(f"Error al editar el cliente: {str(e)}", status=500)


# ==================== NUEVA FUNCIÓN TOKENPERU ====================
@csrf_exempt
def autocompletar_cliente(request):
    """Vista AJAX para autocompletar datos de cliente desde APIs.net.pe"""
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
                'telefono': ''
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
                'telefono': ''
            }
        
        return JsonResponse(response_data)
        
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error: {str(e)}'})