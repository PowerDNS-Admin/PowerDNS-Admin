# GTreeTable 2

GTreeTable is extension of [Tweeter Bootstrap 3](http://getbootstrap.com) framework, which allows to use tree structure inside HTML table.

Thanks to the script it`s possible to create and manage tree with unlimited nesting.

Version 2 of code was completly rewrite and now it's possible to use such functions as: advanced cache, moving nodes by Drag & Drop method, or sorting directly from JavaScript level.

Test available on [demo project](http://gtreetable2.gilek.net).

![](http://gilek.net/images/gtt2-demo.png)

## Enviroment

Till now aplication was test on following browsers:

+ Mozilla Firefox 30,
+ Chrome 37,
+ Internet Explorer 11.

## Minimal installation

1. Firstly add required files:

    ```html
    <link rel="stylesheet" type="text/css" href="gtreetable.min.css" />
    <script type="text/javascript" src="http://code.jquery.com/jquery-2.1.1.min.js"></script>
    <script type="text/javascript" src="bootstrap-gtreetable.js"></script>
    ```

2. Next create empty HTML table:

    ```html
    <table class="table gtreetable" id="gtreetable"><thead><tr><th>Category</th></tr></thead></table>
    ```

3. Inside of method `jQuery.ready` define basic configuration:

    ```javascript
    jQuery('#gtreetable').gtreetable({
      'source': function (id) {
	      return {
	        type: 'GET',
	        url: 'nodeChildren',
	        data: { 'id': id },        
	        dataType: 'json',
	        error: function(XMLHttpRequest) {
	          alert(XMLHttpRequest.status+': '+XMLHttpRequest.responseText);
	        }
	      }
	    }
    });
    ```

More about `source` parameter and returned data format find in [configuration](#configuration) section.

## Functionality

### Actions

Actions defined in `defaultAction` and `actions` parameters are available after indicate or choosing the node.
`defualtActions` includes defualt actions, needed to CUD operations. It may be disabled by set null value.
`actions` defined the actions which may be add after last defined position in `defaultActions`. 

More about action format find in [configuration](#configuration) section.

### CUD

Moment of saving and deleting node can goes together witch server communication by AJAX. Responsible actions: `onSave` and `onDelete`. It's should be functions that return [jQuery.ajax](http://api.jquery.com/jquery.ajax/) settings.

Example configuration:

```javascript
jQuery('#gtreetable').gtreetable({
  'source': function (id) {
    return {
      type: 'GET',
      url: 'nodeChildren',
      data: { 'id': id },        
      dataType: 'json',
      error: function(XMLHttpRequest) {
        alert(XMLHttpRequest.status+': '+XMLHttpRequest.responseText);
      }
    }
  },
  'onSave':function (oNode) {
    return {
      type: 'POST',
      url: !oNode.isSaved() ? 'nodeCreate' : 'nodeUpdate?id=' + oNode.getId(),
      data: {
        parent: oNode.getParent(),
        name: oNode.getName(),
        position: oNode.getInsertPosition(),
        related: oNode.getRelatedNodeId()
      },
      dataType: 'json',
      error: function(XMLHttpRequest) {
        alert(XMLHttpRequest.status+': '+XMLHttpRequest.responseText);
      }
  	};
  },
  'onDelete':function (oNode) {
    return {
      type: 'POST',
      url: 'nodeDelete?id=' + oNode.getId(),
      dataType: 'json',
      error: function(XMLHttpRequest) {
        alert(XMLHttpRequest.status+': '+XMLHttpRequest.responseText);
      }
    };
  }
});
```

The new node may be added in various locations:
+ before chosen node (`before`),
+ after chosen node (`after`),
+ as a first child (`firstChild`),
+ as a last child (`lastChild`).

### Moving

Moving nodes may be realized by using Drag and Drop method.
By default mechanism is disabled, to activate it `draggable` parameter need to be set on true value. Also you need to define `onMove` event. 

At the moment of node dragging, its new locations is marked by pointer with may be located:
+ before the node (`before`),
+ as a last child (`lastChild`), 
+ after the node (`after`).

![](http://gilek.net/images/gtt2-pointer.png)

In this case, application is using additional libraries such as: [jQueryUI](http://jqueryui.com/) and [jQuery Browser Plugin](https://github.com/gabceb/jquery-browser-plugin) so it's necessary to include required files in the code:

```html
<script type="text/javascript" src="http://code.jquery.com/ui/1.11.1/jquery-ui.min.js"></script>
<script type="text/javascript" src="jquery.browser.js"></script>
```
Example configuration:

```javascript
jQuery('#gtreetable').gtreetable({
  'source': function (id) {
    return {
      type: 'GET',
      url: 'nodeChildren',
      data: { 'id': id },        
      dataType: 'json',
      error: function(XMLHttpRequest) {
        alert(XMLHttpRequest.status+': '+XMLHttpRequest.responseText);
      }
    }
  },
  'draggable': true,
  'onMove': function (oSource, oDestination, position) {
    return {
      type: 'POST',
      url: 'nodeMove?id=' + oNode.getId(),
      data: {
        related: oDestination.getId(),
        position: position
      },
      dataType: 'json',
      error: function(XMLHttpRequest) {
        alert(XMLHttpRequest.status+': '+XMLHttpRequest.responseText);
      }
    }; 
  }    
});
```

### Choosing

To choose the node it's needed to click on its name. Depending on `selectLimit` parameter it's possible to indicate one or more nodes.

In this case it's worth to pay attention on a few events triggered in the moment of:
+ selecting node (`onSelect`),
+ unselecting node (`onUnselect`),
+ when limit of selection is overflowed (`onSelectOverflow`).

More information about [configuration](#configuration):

### Sorting

Node sorting function inside of tree may be realized directly from JavaScript level. Only needed to define sorting method as `sort` parameter function.

Sorting operation is triggered during: expanding tree branches, adding new node and existing node name edition.

Working of sorting function is the same as in case of [table sorting](https://developer.mozilla.org/pl/docs/Web/JavaScript/Referencje/Obiekty/Array/sort), so example of configuration may look as follow:

```javascript
jQuery('#gtreetable').gtreetable({
  'source': function (id) {
    return {
      type: 'GET',
      url: 'nodeChildren',
      data: { 'id': id },        
      dataType: 'json',
      error: function(XMLHttpRequest) {
        alert(XMLHttpRequest.status+': '+XMLHttpRequest.responseText);
      }
    }
  },
  'sort': function (a, b) {          
    var aName = a.name.toLowerCase();
    var bName = b.name.toLowerCase(); 
    return ((aName < bName) ? -1 : ((aName > bName) ? 1 : 0));                            
  }  
}); 
```

### Nodes types

Depending on node type is possible to display additional icon next to its name. Nodes type definition is based on `types` parameter.

Example configuration:

```javascript
jQuery('#gtreetable').gtreetable({
  'source': function (id) {
    return {
      type: 'GET',
      url: 'nodeChildren',
      data: { 'id': id },        
      dataType: 'json',
      error: function(XMLHttpRequest) {
        alert(XMLHttpRequest.status+': '+XMLHttpRequest.responseText);
      }
    }
  },
  'types': { default: 'glyphicon glyphicon-folder-open'}
});
```

Adding various node type is realized by `GTreeTableNode.add(String position, String type)` method.

![](http://gilek.net/images/gtt2-type.png) 
 
### Translations

User interface elements by default are displayed in English. There is a possibility to change language by change `language` parameter and attaching appropriate files:

Example configuration:

```html
<script type="text/javascript" src="languages/bootstrap-gtreetable.pl.js"></script>
```

```javascript
jQuery('#gtreetable').gtreetable({
  'source': function (id) {
    return {
      type: 'GET',
      url: 'nodeChildren',
      data: { 'id': id },        
      dataType: 'json',
      error: function(XMLHttpRequest) {
        alert(XMLHttpRequest.status+': '+XMLHttpRequest.responseText);
      }
    }
  },
  'language': 'pl'
});
```

In the moment when some position from translations can't be found then its values stays unchanged. 

### Cache

In relation to 1.x version, cache mechanism was improved. It's possible to work in 3 levels:
+ 0 - mechanism off,
+ 1 - information about child nodes are stored in memory. After moving or CUD operation, redownload information from data base is required,
+ 2 - as in 1 level with the difference that all operation on nodes are mapping in cache.

There is possibility to force refesh data by pushing <kbd>Alt</kbd> in the moment of node expanding.

## <a name="configuration"></a>Configuration

### Parameters

+ `actions` (Array) - set of actions, which should be added after the last position defined in `defaultActions` parameter. More info about required data format is located in description of  `defaultActions` parameter.

+ `cache (Integer)` - define whether actual node state should be stored in cache. It's possible to work in 3 levels:
  + 0 - mechanism off,
  + 1 - partial mapping. In the moment of moving or CUD operation the state of depending nodes is resetting, 
  + 2 - fully mapping.

+ `classes` (Object) - parameter consists set of CSS class using to build user interface.

+ `defaultActions` (Array) - set of default CUD actions. Parameter needs to be table consists of objects in following format:

    ```javascript
    {
      name: 'Action label',
      event: function (oNode, oManager) { } // code to execute 
    }
    ```

    Separator (horizontal line) defined by following construction (object):
    
    ```javascript
    { divider: true }
    ```

    When action label is surrounded by bracket and preceded by $ i.e. `${actionEdit}` then its value is translated on `language` parameter language. 

+ `dragCanExpand` (boolean) - define whether during node moving is possible to expand other nodes after choosing appropriate icon. 	

+ `draggable` (boolean) - define whether nodes can be moved. Parameter value changing on true is related with necessity of adding required [jQueryUI](http://jqueryui.com/) library:
  + core,
  + widget,
  + position,
  + mouse,
  + draggable,
  + droppable.

+ `inputWidth` (String) - width of field of adding / edition  node name.

+ `language` (String) - user interface language. Default English, change of language is related with necessity of adding translation file. In the moment when some translated position won't be found, then its value stays in English.

+ `manyroots` (boolean) - define whether it's possible to create multiple nodes roots.

+ `selectLimit` (Integer) - define nodes selection behavours:
  + > 1 - indicate exactly the same number of nodes,
  + 0 - selection disabled,
  + -1 - unlimited selection.    

+ `nodeIndent` (Integer) - Distance between node and its container. The value is multiplied, depending on node level.

+ `nodeLevel` (Integer)

+ `nodesWrapper` (String) - define nodes wrapper property. Default `nodes`. [More info](https://github.com/gilek/bootstrap-gtreetable/issues/9).

+ `readonly` (boolean) - determines whether executing action on node is possible or not.

+ `showExpandIconOnEmpty` (boolean) - parameter set on true value means that expanding node icon stays visible all the time, even if there is no node child. 

+ `sort` (callback (GTreeTableNode oNodeA, GTreeTableNode oNodeB)) - sorting function triggered in the moment of: displaying nodes, adding new one or its changing. Working of sorting function is the same as in case of [table sorting](https://developer.mozilla.org/pl/docs/Web/JavaScript/Referencje/Obiekty/Array/sort).

	  Example of sorting by node name in the ascending order. 

    ```javascript
    function (a, b) {          
      var aName = a.name.toLowerCase();
      var bName = b.name.toLowerCase(); 
      return ((aName < bName) ? -1 : ((aName > bName) ? 1 : 0));                            
    }
    ```
 

+ `source` (callback (Integer id))<a name="source"></a> - function must return `jQuery.ajax` settings, responsible for getting nodes from data base.

    If ID = 0, then tree roots should be returned.
    
	  Information about nodes should be included in the object table in JSON format:

    ```JSON
    {
      "id": "node ID",
      "name": "node name",
      "level": "node level", 
      "type": "node type" 
    }
    ```
+ `template` (String)

+ `templateParts` (Object) 

+ `types` (Object) - object consists relations between node types and its icon class i.e.

    ```javascript
    { default: "glyphicon glyphicon-folder-open" }
    ```

### Events

+ `onDelete(GTreeTableNode node)` - event triggering at the node deleting moment, must return `jQuery.ajax` settings.

+ `onMove(GTreeTableNode node, GTreeTableNode destination, string position)` - event triggering at the node moving moment, must return `jQuery.ajax` settings.

+ `onSave(GTreeTableNode node)` - event triggering at the node adding / edition moment. It must return `jQuery.ajax` settings.

+ `onSelect(GTreeTableNode node)` - event triggering at the node selecting moment.

+ `onSelectOverflow(GTreeTableNode node)` - event triggering when `selectLimit` parameter is positive number and selecting another node would be related with overflow of defined quantity.

+ `onUnselect(GTreeTableNode node)` - event triggering at the moment when node is unselected.

### Methods (chosen)

+ `GTreeTableManager.getSelectedNodes()` - returns table of selected nodes.

+ `GTreeTableNode.getPath(GTreeTableNode oNode)` -  returns table consists the node path i.e.:
		
    ```javascript
    ["Node name", "Parent node", "Main node"]	
    ```

## Server side

GTreeTable offer supports only in JavaScript level. Special extensions of Yii framework [yii2-gtreetable](https://github.com/gilek/yii2-gtreetable) or [yii-gtreetable](https://github.com/gilek/yii-gtreetable) can be use as server side application. Even if you don't use this software every day, don't worry in the near future will be prepared special library (written in native PHP), designed to realize this task.
