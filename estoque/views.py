from django.shortcuts import render



# Create your views here.
def lista_categoria(request):

    return render(request, 'estoque/categoria/lista.html')


def lista_estoque(request):

    return render(request, 'estoque/produto/lista.html')