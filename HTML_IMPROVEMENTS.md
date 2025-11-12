# Améliorations de la Structure HTML

## Résumé des Améliorations

Ce document décrit les améliorations apportées à la structure HTML pour rendre les articles plus professionnels et plus lisibles.

## 1. Centrage de la Zone de Texte (Marge à Marge)

### Avant
- Container avec `max-width: 1200px` et padding
- Contenu non centré avec marges inégales

### Après
- Container sans padding (`padding: 0`)
- Zone de contenu interne (`article-inner`) avec `max-width: 1000px` et `margin: 0 auto`
- Contenu centré avec marges égales de chaque côté
- Padding responsive : 50px (desktop), 60px (tablet), 25px (mobile)

**Code CSS :**
```css
.article-container {
  max-width: 1200px;
  margin: 40px auto;
  padding: 0;  /* Pas de padding sur le container */
}

.article-inner {
  max-width: 1000px;
  margin: 0 auto;  /* Centrage automatique */
  padding: 40px 50px 50px 50px;  /* Marges égales */
}
```

## 2. Citations en Liens Hypertexte

### Fonctionnalité
- Les citations `[source: filename.html]` sont automatiquement converties en liens cliquables
- Support des citations multiples : `[source: file1.html] and [source: file2.html]`
- Liens pointent vers `../data/raw/filename.html`

### Format
- **Citation simple** : `[source: article-name.html]` → Lien cliquable
- **Citations multiples** : `[source: file1.html] and [source: file2.html]` → Plusieurs liens séparés par "and"

### Style
- Citations en italique, couleur grise
- Liens avec bordure pointillée, couleur Guardian blue (#052962)
- Hover : bordure solide
- Taille de police légèrement réduite (0.9em)

**Exemple de rendu :**
```html
<span class="citation">[source: <a href="../data/raw/article.html" class="source-citation">article.html</a>]</span>
```

## 3. Pull Quotes (Citations Mises en Évidence)

### Fonctionnalité
- Détection automatique des citations importantes dans le texte
- Extraction des citations entre guillemets (20-150 caractères)
- Affichage dans un bloc stylisé séparé du texte principal

### Style
- Bloc centré avec fond bleu clair (#f0f4f8)
- Bordures gauche et droite bleues (#052962)
- Guillemets décoratifs en grand format
- Police Merriweather, italique, taille 24-28px
- Largeur maximale : 80% (desktop), 90% (mobile)

### Détection
- Recherche de citations entre guillemets doubles ou typographiques
- Longueur optimale : 20-150 caractères
- Extraction automatique et affichage après le paragraphe

**Exemple de rendu :**
```html
<blockquote class="pull-quote">
  "This is an important quote that will be highlighted"
</blockquote>
```

## 4. Gestion des Citations Multiples

### Fonctionnalité
- Support des citations multiples dans une même référence
- Format : `[source: file1.html] and [source: file2.html]`
- Format alternatif : `[source: file1.html, file2.html]`
- Chaque source devient un lien séparé

### Rendu
- **Citation unique** : `[source: article.html]`
- **Citations multiples** : `[sources: article1.html, article2.html and article3.html]`
- Tous les liens sont cliquables et stylisés de la même manière

### Parsing
- Détection par regex : `\[source:\s*([^\]]+)\]`
- Séparation par "and" ou virgule
- Nettoyage automatique des espaces

## Détails Techniques

### Nouvelles Fonctions

1. **`_process_citations(text: str) -> str`**
   - Convertit les citations en liens HTML
   - Gère les citations simples et multiples
   - Retourne le texte avec les liens intégrés

2. **`_detect_pull_quote(text: str) -> tuple[str, Optional[str]]`**
   - Détecte les citations importantes
   - Extrait la citation du texte
   - Retourne (texte_restant, citation) ou (texte, None)

3. **`_render_pull_quote(quote: str) -> str`**
   - Génère le HTML pour un pull quote
   - Applique le style approprié

### Modifications CSS

#### Citations
```css
.citation {
  font-size: 0.9em;
  color: #666;
  font-style: italic;
}

.source-citation {
  color: #052962;
  font-weight: 500;
  border-bottom: 1px dashed rgba(5, 41, 98, 0.4);
}
```

#### Pull Quotes
```css
.pull-quote {
  font-family: 'Merriweather', Georgia, serif;
  font-size: 24px;
  line-height: 1.5;
  color: #052962;
  font-style: italic;
  margin: 30px 0;
  padding: 20px 30px;
  border-left: 4px solid #052962;
  border-right: 4px solid #052962;
  background-color: #f0f4f8;
  text-align: center;
  max-width: 80%;
  margin-left: auto;
  margin-right: auto;
}
```

## Responsive Design

### Mobile (< 768px)
- Padding réduit : 30px 25px
- Pull quotes : 20px, max-width 90%

### Tablet (768px - 1023px)
- Padding : 50px 60px
- Pull quotes : 26px, padding 25px 35px

### Desktop (≥ 1024px)
- Padding : 50px 80px
- Pull quotes : 28px, max-width 70%

## Exemples d'Utilisation

### Citation Simple
**Texte source :**
```
According to [source: article.html], the research shows...
```

**Rendu HTML :**
```html
According to <span class="citation">[source: <a href="../data/raw/article.html" class="source-citation">article.html</a>]</span>, the research shows...
```

### Citations Multiples
**Texte source :**
```
Research from [source: article1.html] and [source: article2.html] indicates...
```

**Rendu HTML :**
```html
Research from <span class="citation">[sources: <a href="../data/raw/article1.html" class="source-citation">article1.html</a>, <a href="../data/raw/article2.html" class="source-citation">article2.html</a>]</span> indicates...
```

### Pull Quote
**Texte source :**
```
The expert stated that "This breakthrough will change everything we know about AI technology" during the conference.
```

**Rendu HTML :**
```html
<p class="paragraph">The expert stated that during the conference.</p>
<blockquote class="pull-quote">This breakthrough will change everything we know about AI technology</blockquote>
```

## Avantages

1. **Meilleure lisibilité** : Contenu centré avec marges égales
2. **Navigation améliorée** : Citations cliquables pour accéder aux sources
3. **Engagement visuel** : Pull quotes mettent en évidence les points clés
4. **Professionnalisme** : Style cohérent et moderne
5. **Accessibilité** : Liens clairs et bien stylisés

## Compatibilité

- ✅ Compatible avec tous les navigateurs modernes
- ✅ Responsive sur tous les appareils
- ✅ Accessible (liens clairs, contrastes appropriés)
- ✅ Rétrocompatible (fonctionne avec les anciens formats de citations)

