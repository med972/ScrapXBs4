#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  2 21:37:41 2017

@author: mehdiregina
"""

import requests
import json
from bs4 import BeautifulSoup
import functools
import time
from multiprocessing import Pool

def get_soup_from_url(url):
    
    page=requests.get(url);
    if (page.status_code == 200):
        return BeautifulSoup(page.content,'html.parser')
    else:
        return None

def get_top(url, nb):
    soup=get_soup_from_url(url)
    
    #je sélection tous les tags tr contenus dans un tag tbody
    #attention d'autres combinaisons tbody -> tr existe après le top : considérer les 256 premiers tags
    liste_row=soup.select("tbody tr")[0:nb]
    
    
    liste_rank = [row.find("th").get_text() for row in liste_row]
    liste_name = [row.select("td:nth-of-type(1)")[0].find("a").get_text() for row in liste_row]
    liste_contribs = [int(row.select("td:nth-of-type(2)")[0].get_text()) for row in liste_row]
    liste_location = [row.select("td:nth-of-type(3)")[0].get_text() for row in liste_row]
    
    return liste_rank,liste_name,liste_contribs,liste_location


def get_star_mean(user):
    #commande get & user/repos renvoie la liste des repos associés au user
    url = "https://api.github.com/users/"+user+"/repos"
      
    #header pour l'autentification, (le mdp n'estpas entré)
    header = {"Authorization" : "Basic mdp_encrypt" }
    page = requests.get(url,headers = header)
    
    #j'instancie mon json object sur la base de page.content
    json_obj = json.loads(page.content)
    
    #je recupère dans chaque dico repo l'info nb étoiles contenu dans 'stargazers_count'
    liste_star=[dico_repo['stargazers_count'] for dico_repo in json_obj]
    
    #je retourne la moyenne d'étoiles
    if (len(liste_star) !=0):
        return functools.reduce(lambda x,y : x+y, liste_star)/double(len(liste_star))
    else :
        return 0


#Main sequenciel
debut = time.time()
liste_rank,liste_name,liste_contribs,liste_location = get_top("https://gist.github.com/paulmillr/2657075",256)
liste_star_mean=[get_star_mean(name) for name in liste_name]
print(liste_star_mean)


fin = time.time()
print("-------")
print(fin-debut)    

#main multi processing
p = Pool(4)
debut = time.time()
#multiprocessing fonctionne avec la fonction map
#en param la fonction à appliquer sur chaque élément, et le conteneur des éléments
liste_star_mean=p.map(get_star_mean,liste_name)

fin = time.time()
print("-------")
print(fin-debut)  




