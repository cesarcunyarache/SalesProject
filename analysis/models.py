
from django.db import models

class Sale(models.Model):
    producto = models.CharField(max_length=100)
    cantidad = models.IntegerField()
    precio = models.FloatField()
    fecha = models.DateField()

    def __str__(self):
        return f"{self.producto} - {self.cantidad} units at ${self.precio}"
