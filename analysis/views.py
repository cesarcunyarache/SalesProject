# Create your views here.
# analysis/views.py
import csv

from django.http import HttpResponse
from django.shortcuts import render
from .models import Sale
from .forms import UploadFileForm
from io import TextIOWrapper

def upload_file(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            data = TextIOWrapper(request.FILES['file'].file, encoding='utf-8')
            reader = csv.reader(data)
            for row in reader:
                Sale.objects.create(producto=row[0], cantidad=int(row[1]), precio=float(row[2]), fecha=row[3])
            return render(request, 'upload_success.html')
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})


def analyze_data(request):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')  # Cambia el backend de Matplotlib para evitar problemas con la GUI en macOS
    import matplotlib.pyplot as plt
    from prettytable import PrettyTable
    import networkx as nx
    import math
    from sympy import symbols, diff
    from io import BytesIO
    import base64

    sales = Sale.objects.all()
    productos = [sale.producto for sale in sales]
    cantidades = np.array([sale.cantidad for sale in sales])
    precios = np.array([sale.precio for sale in sales])

    # Numpy: Cálculos Numéricos
    ingresos_total = sum(cantidades * precios)
    media_precios = np.mean(precios)

    # Math
    ingreso_inicial = sum(cantidades * precios)  # Ingreso inicial en el día 0
    tasa_crecimiento = 0.03  # Tasa de crecimiento diario del ingreso total (3%)
    ingresos_predichos = ingreso_inicial * math.exp(tasa_crecimiento * 5)  # Aplicación de la función exponencial

    # Matplotlib: Visualización de Datos
    plt.figure()
    plt.plot(productos, cantidades , label='Cantidades Vendidas')
    plt.legend()
    plt.title('Cantidades Vendidas')
    plt.xlabel('Indice')
    plt.ylabel('Cantidad')
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()

    # PrettyTable: Genera tablas simples
    table = PrettyTable()
    table.field_names = ["Producto", "Cantidad", "Precio"]
    for sale in sales:
        table.add_row([sale.producto, sale.cantidad, sale.precio])
    table_html = table.get_html_string()

    # NetworkX: Manejo y Visualización de Grafos
    G = nx.Graph()
    for sale in sales:
        producto = sale.producto
        cantidad = sale.cantidad
        precio = sale.precio
        if producto not in G.nodes:
            G.add_node(producto, cantidad_vendida=0, ingreso_total=0)
        G.nodes[producto]['cantidad_vendida'] += cantidad
        G.nodes[producto]['ingreso_total'] += cantidad * precio

    # Visualizar el grafo
    plt.figure(figsize=(12, 6))
    node_size = [G.nodes[n]['ingreso_total'] for n in G.nodes()]
    nx.draw(G, with_labels=True, node_color='skyblue', node_size=node_size, font_size=10)
    plt.title("Grafo de Productos basado en Ventas")
    plt.tight_layout()


    # Guardar la imagen del grafo en formato PNG y convertirla a base64
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    graph_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()

    # Sympy: Manipulación y Resolución de Expresiones Simbólicas
    ventas = [(sale.producto, sale.cantidad, sale.precio) for sale in sales]

    # Definir el símbolo P que representa el precio
    P = symbols('P')

    # Función de demanda lineal
    def demanda(a, b, P):
        return a - b * P

    # Calcular las ventas totales para cada producto
    ventas_totales = [(producto, cantidad, precio, cantidad * precio) for producto, cantidad, precio in ventas]

    # Encontrar el producto con más ventas totales
    producto_mas_vendido = max(ventas_totales, key=lambda venta: venta[3])

    # Extraer los datos del producto más vendido
    nombre_producto, cantidad_inicial, precio_inicial, _ = producto_mas_vendido

    # Definir cantidad final y precio final para la elasticidad (pequeña variación)
    cantidad_final = cantidad_inicial - 1
    precio_final = precio_inicial + 1

    # Calcular 'a' y 'b' para la demanda lineal
    a = cantidad_inicial
    b = (cantidad_final - cantidad_inicial) / (precio_inicial - precio_final)

    # Calcular la elasticidad precio de la demanda
    elasticidad = diff(demanda(a, b, P), P) * (P / demanda(a, b, P))

    # Evaluar la elasticidad en el precio inicial
    elasticidad_evaluada = elasticidad.subs(P, precio_inicial)

    context = {
        'ingresos_total': f"{ingresos_total:.2f}",
        'media_precios': media_precios,
        'ingresos_predichos': f"{ingresos_predichos:.2f}",
        'producto_mas_vendido': nombre_producto,
        'elasticidad': elasticidad_evaluada,
        'image_base64': image_base64,
        'table_html': table_html,
        'graph_base64': graph_base64,

    }

    return render(request, 'analysis.html', context)
