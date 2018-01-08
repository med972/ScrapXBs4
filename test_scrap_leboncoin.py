#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 14 20:44:19 2017

@author: mehdiregina
"""
import requests
from bs4 import BeautifulSoup
import time
from multiprocessing import Pool
import pandas as pd
import re
import json

region = ["ile_de_france","acquitaine","provence_alpes_cote_d_azur"]
type_vendeur = ["professionnel","particulier"]
models = ["INTENS","LIFE","ZEN"]
url_centrale = "http://www.lacentrale.fr/cote-voitures-renault-zoe--2013-.html"

def get_soup(url, method='get', data={}):
    """Retourne le soup object associé à la page"""
    if (method == 'get'):
        page = requests.get(url)
    elif (method == 'post'):
        page = requests.post(url, data=data)
    else:
        return None
    
    if (page.status_code == 200):
        soup = BeautifulSoup(page.content, 'html.parser')
        return soup
    else:
        return None


def get_nb_page(url_lbc):
    """Retourne le nombre de pages associées à une url en type str"""
    soup = get_soup(url_lbc)
    res = soup.find_all("span", {"class":"total_page"})
    return res[0].get_text()


def get_list_cars_url (region,type_vendeur):
    """Retourne la liste des zoe en vente associée à la région (web crawling)"""
    liste_url = list()
    
    if(type_vendeur.lower() not in type_vendeur ) :
        raise NameError ('type vendeur doit être particulier ou professionnel' )
        return None
    else:
        if(type_vendeur.lower()=="particulier"):
            type_v='p'
        else:
            type_v='c'
        #je recupère le nb de page en bas de la page 1
        nb_page = get_nb_page("https://www.leboncoin.fr/annonces/offres/"+region+"/?f="+type_v)
    
        for i in range(1,3) :
            url = "https://www.leboncoin.fr/annonces/offres/"+region+"/?o="+str(i)+"&q=renault%20zoe&f="+type_v
            soup = get_soup(url)
            #Possible via find/find_all de faire appel aux attributs d'un tag
            liste_annonce = soup.find_all("a",{"class":"list_item"})
            #je parcours les liste et si ZOE est dans la desc je recupère l'url
            liste_url_page = [annonce["href"] for annonce in liste_annonce if "voitures" in annonce["href"]]
            #je stocke les liste des différentes pages
            liste_url += liste_url_page
        return (liste_url,type_vendeur.lower())


def get_car_data (url,type_vendeur):
    """Retourne les infos année, kilométrage, prix, téléphone du propriétaire associée à un url de voiture"""
    soup = get_soup('https:'+url)
    #le 1er tag span contenant l'attribut class=value est le prix
    res = soup.find('span',{'class':'value'})
    prix = int("".join(res.get_text().strip().strip("nbsp;€").split(" ")))
    
    #on retrouve le tag de l'année via un attribut
    res = soup.find('span',{'itemprop':'releaseDate'})
    annee = int(res.get_text().strip())
    
    #aucun tag particulier pour le kilometrage, je prends donc la 5e combinaison tag/value
    res = soup.find_all('span',{'class':'value'})
    kilometrage = int("".join(res[5].get_text().strip('KM').split(" ")))
    
    #numero tel & modele sont inclus dans la description
    #regex non correcte
    description = soup.find('p',{'class':'value'}).get_text()
    modele = re.findall(r'((?i)(INTENS)|(LIFE)|(ZEN))',description)
    if (len(modele)>0):
        modele = modele[0][0].lower()
    else:
        modele = "n/a"
    
    numero = re.findall(r'([0-9]{10}|([0-9]{2}[-]){4}[0-9]{2}|([0-9]{2}\s){4}[0-9]{2})', description)
    if (len(numero)>0):
        numero = numero[0][0]
    else:
        numero = "n/a"
    
    
    #Numero de département : utile pour calculer l'argus
    res = soup.find('span',{'itemprop':'address'})
    numero_dpt = res.get_text().split()[1]
    
    #ajouter methode l'argus dans cette méthode
    cote = int(get_argus(numero_dpt,kilometrage,modele))
    
    return modele, annee, kilometrage,prix,cote,numero,type_vendeur


def get_url_argus(modele) :
   """Retourne l'url associé au modèle"""
   soup = get_soup(url_centrale)
   liste_div = soup.find_all("div",{'class':'listingResultLine'})
   for i in range(0,len(liste_div)):
       if modele in liste_div[i].find('a')['href']:
           break
   return "https://www.lacentrale.fr/"+liste_div[i].find('a')['href']
   
        

def get_argus (departement,km,modele):
   """Retourne le prix d'argus associé à un certain type de voiture"""
   #cookies ={'php_sessid':'184f599bac6d29813b00c587f09a4b2c',
    #         'xtvrn':'$251312$','xtant251312':'1','xtan251312':'-','user_type':'vendeur','tCdebugLib':'1',
     #        'retargeting_data':'B','_mob_':'0','__uzmdj2':'1508412478','__uzmd':'1508412477',
      #       '__uzmcj2':'971904941100','__uzmc':'106859465202','__uzmbj2':'1508005130','__uzmb':'150800510',
       #      '__uzmaj2':'zmaj2	d0c8096c-af88-442b-b988-a610595cef9d'}
   #request_url = "https://www.lacentrale.fr/get_co_prox.php?km="+km+"&zipcode="+departement+"&month=01"
   #page_json = requests.get("https://www.lacentrale.fr/get_co_prox.php?km="+km+"&zipcode="+departement+"&month=01",param=cookies)
   #prix= json.loads(page_json.content)
   url_argus = get_url_argus(modele)
   soup = get_soup(url_argus)
   cote = "".join(soup.find('span',{'class':'jsRefinedQuot'}).get_text().split())
   return cote
    
#Main
#Je stocke les données voitures dans des listes
liste = get_list_cars_url("ile_de_france","professionnel")
liste2 = [get_car_data(url,liste[1]) for url in liste[0]]
#Exemple pour les données ile de france professionnel
df = pd.DataFrame(data=liste2,columns=["Modele","Annee","Km","Prix","Cote","Numero","Type"],)
df["Prix>Cote"] = df["Prix"]>df["Cote"]
print(df)



