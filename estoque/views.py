from django.shortcuts import render

# Create your views here.
def lista_estoque(request):

    return render(request, 'estoque/lista.html')