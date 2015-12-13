/* ========================================================= 
 * bootstrap-gtreetable v2.2.1-alpha
 * https://github.com/gilek/bootstrap-gtreetable
 * ========================================================= 
 * Copyright 2014 Maciej Kłak
 * Licensed under MIT (https://github.com/gilek/bootstrap-gtreetable/blob/master/LICENSE)
 * ========================================================= */

(function ($) {
    // GTREETABLE CLASSES DEFINITION
    // =============================    
    function GTreeTable(element, options) {
        this.options = options;
        this.$tree = $(element);
        this.language = this.options.languages[this.options.language] === undefined ?
            this.options.languages['en-US'] :
            $.extend({}, this.options.languages['en-US'], this.options.languages[this.options.language]);
        this._isNodeDragging = false;
        this._lastId = 0;
        
        this.actions = [];
        if (this.options.defaultActions !== null) {
            this.actions = this.options.defaultActions;
        }

        if (this.options.actions !== undefined) {
            this.actions.push.apply(this.actions, this.options.actions);
        }        
        
        if (this.options.cache > 0) {
            this.cacheManager = new GTreeTableCache(this);
        }
        
        var lang = this.language;
        this.template = this.options.template !== undefined ? this.options.template : 
           '<table class="table gtreetable">' +
           '<tr class="' + this.options.classes.node + ' ' + this.options.classes.collapsed + '">' +
           '<td>' +
           '<span>${draggableIcon}${indent}${ecIcon}${selectedIcon}${typeIcon}${name}</span>' +
           '<span class="hide ' + this.options.classes.action + '">${input}${saveButton} ${cancelButton}</span>' +
           '<div class="btn-group pull-right ' + this.options.classes.buttons + '">${actionsButton}${actionsList}</div>' +
           '</td>' +
           '</tr>' +
           '</table>';            

      this.templateParts = this.options.templateParts !== undefined ? this.options.templateParts :
            {
                draggableIcon: this.options.draggable === true ? '<span class="' + this.options.classes.handleIcon + '">&zwnj;</span><span class="' + this.options.classes.draggablePointer + '">&zwnj;</span>'  : '',
                indent: '<span class="' + this.options.classes.indent + '">&zwnj;</span>',
                ecIcon: '<span class="' + this.options.classes.ceIcon + ' icon"></span>',
                selectedIcon: '<span class="' + this.options.classes.selectedIcon + ' icon"></span>',
                typeIcon: '<span class="' + this.options.classes.typeIcon + '"></span>',
                name: '<span class="' + this.options.classes.name + '"></span>',
                input: '<input type="text" name="name" value="" style="width: ' + this.options.inputWidth + '" class="form-control" />',
                saveButton: '<button type="button" class="btn btn-sm btn-primary ' + this.options.classes.saveButton + '">' + lang.save + '</button>',
                cancelButton: '<button type="button" class="btn btn-sm ' + this.options.classes.cancelButton + '">' + lang.cancel + '</button>',
                actionsButton: '<button type="button" class="btn btn-sm btn-default dropdown-toggle" data-toggle="dropdown">' + lang.action + ' <span class="caret"></span></button>',
                actionsList: ''
            };
            
        if (this.actions.length > 0) {
            var templateActionsList = '<ul class="dropdown-menu" role="menu">' +
            '<li role="presentation" class="dropdown-header">' + lang.action + '</li>';

            $.each(this.actions, function (index, action) {
                if (action.divider === true) {
                    templateActionsList += '<li class="divider"></li>';
                } 
                else {
                    var matches = action.name.match(/\$\{([\w\W]+)\}/),
                        name = matches !== null && matches[1] !== undefined && lang.actions[matches[1]] !== undefined ? lang.actions[matches[1]] : action.name;
                    templateActionsList += '<li role="presentation"><a href="#notarget" class="node-action-' + index + '" tabindex="-1">' + name + '</a></li>';
                }
            });        

            templateActionsList += '</ul>';
            this.templateParts.actionsList = templateActionsList;
        }
        
        var template = this.template;

        $.each(this.templateParts, function(index, value) {
            template = template.replace('${'+index+'}', value);
        });
        
        this.options.template = template;
        

        if (this.$tree.find('tbody').length === 0) {
            this.$tree.append('<tbody></tbody>');
        }

        if (!this.options.readonly) {
            this.$tree.addClass('gtreetable-fullAccess');
        }

        this.$nodeTemplate = $(this.options.templateSelector !== undefined ? 
            this.options.templateSelector : 
            this.options.template).find('.' + this.options.classes.node);
          
        if (this.options.draggable === true) {
            this.isNodeDragging(false);
        }
        this.init();
    }

    GTreeTable.prototype = {

        getNode: function ($node) {
            return $node.data('bs.gtreetable.gtreetablenode');
        },

        getNodeById: function (id) {
            return this.getNode(this.$tree.find('.' + this.options.classes.node + "[data-id='" + id + "']"));
        },

        getSelectedNodes: function () {
            var selectedNodes = [],
                that = this;
            $.each(this.$tree.find('.' + this.options.classes.selected), function () {
                selectedNodes.push(that.getNode($(this)));
            });

            return selectedNodes;
        },

        getSourceNodes: function (nodeId, force) {
            var that = this,
                oNode = this.getNodeById(nodeId),
                cached = (nodeId > 0 && this.options.cache > 0);
                
            if (cached && force !== true) {
                var data = this.cacheManager.get(oNode);
                if (data !== undefined) {
                    var temp = {};
                    temp[that.options.nodesWrapper] = data;
                    return temp;

                }
            }
            
            var sourceOptions = this.options.source(nodeId);
            var defaultSourceOptions = {
                beforeSend: function () {
                    if (nodeId > 0) {
                        oNode.isLoading(true);
                    }
                },
                success: function (result) {
                    if (result[that.options.nodesWrapper] !== undefined) {
                        data = result[that.options.nodesWrapper];
                        for (var x = 0; x < data.length; x += 1) {
                            data[x].parent = nodeId;
                        }

                        if (typeof that.options.sort === "function") {
                            data.sort(that.options.sort);
                        }

                        if (cached) {
                            that.cacheManager.set(oNode, data);
                        }
                    }
                },
                error: function (XMLHttpRequest) {
                    alert(XMLHttpRequest.status + ': ' + XMLHttpRequest.responseText);
                },
                complete: function () {
                    if (nodeId > 0) {
                        oNode.isLoading(false);
                    }
                }
            };

            return $.ajax($.extend({}, defaultSourceOptions, sourceOptions));
        },
        
        init: function () {
            var that = this;

            this.getSourceNodes(0).done(function (result) {
                var data = result[that.options.nodesWrapper];
                for(var x in data) {
                    var oNewNode = new GTreeTableNode(data[x], that);
                    oNewNode.insertIntegral(oNewNode);
                }
            });
        },
                     
        isNodeDragging: function(action) {
            if (action === undefined) {
                return this._isNodeDragging;
            } else if (action === true) {
                this._isNodeDragging = true;
                this.$tree.disableSelection();
            } else {
                this._isNodeDragging = false;
                this.$tree.enableSelection();
            }
        },
        
        generateNewId: function() {
            this._lastId += 1;
            return 'g' + this._lastId;
        }
    };

    function GTreeTableNode(data, gtreetable) {
        this.manager = gtreetable;

        this.level = parseInt(data.level);
        this.parent = data.parent;
        this.name = data.name;
        this.type = data.type;
        this.id = data.id;

        this.insertPosition = undefined;
        this.movePosition = undefined;
        this.relatedNodeId = undefined;
        this._isExpanded = false;
        this._isLoading = false;
        this._isSaved = data.id === undefined ? false : true;
        this._isSelected = false;
        this._isHovered = false;
        this._isEditable = false;

        this.init();
    }

    GTreeTableNode.prototype = {
        
        getPath: function () {
            var oNode = this, 
                path = [oNode.name],
                parent = oNode.parent;

            oNode.$node.prevAll('.' + this.manager.options.classes.node).each(function () {
                var currentNode = oNode.manager.getNode($(this));
                if (currentNode.id === parent) {
                    parent = currentNode.parent;
                    path[path.length] = currentNode.name;
                }
            });
            return path;
        },        

        getParents: function () {
            var parents = [],
            parentId = this.parent;
            
            while (true) {
                if (parentId === 0) {
                    break;
                }
                
                var oNode = this.manager.getNodeById(parentId);
                parents.push(oNode);
                parentId = oNode.parent;
                
            }
            return parents;        
        },   
        
        //TODO
        // potrzebne tylko w przypadku cache
        getIP: function() {
            var oNode = this,
                ip = '0';
        
            var parents = oNode.getParents();
            parents.reverse();
            $.each(parents, function() {
                ip += '.'+this.id;
            });
            
            ip += '.'+oNode.id;

            return ip;
        },
        
        getSiblings: function () {
            var oNode = this,
                siblings = [],
                findPath = '.' + oNode.manager.options.classes.node + "[data-parent='" + oNode.parent + "']",
                prev = oNode.$node.prevAll(findPath); 
                
            for (var i = prev.length-1; i >= 0; --i) { 
                siblings.push(oNode.manager.getNode($(prev[i])));
            }               
                    
            siblings.push(oNode);    
                    
            oNode.$node
                 .nextAll(findPath)
                 .each(function () {
                     siblings.push(oNode.manager.getNode($(this)));
                 });  
                 
            return siblings;        
        },
        
        getDescendants: function (options) {
            var oParentNode = this,
                settings = $.extend({},{
                    depth: 1,
                    includeNotSaved: false,
                    index: undefined
                },options),
                findPath = '.' + oParentNode.manager.options.classes.node,
                depth = settings.depth !== -1 || isNaN(settings.depth) ? settings.depth : Infinity,
                descendants = [];
        
            if ((settings.includeNotSaved === false)) {
                findPath += '.' + oParentNode.manager.options.classes.saved;
            }
            
            if (depth > 1) {
                oParentNode.$node.nextAll(findPath).each(function () {
                    var oCurrentNode = oParentNode.manager.getNode($(this));
                    if ( (oCurrentNode.level <= oParentNode.level) || (oCurrentNode.level === oParentNode.level && oCurrentNode.parent === oParentNode.parent) ) {
                        if (!(settings.includeNotSaved === true && !oCurrentNode.isSaved())) {
                            return false;
                        }
                    } 
                    descendants.push(oCurrentNode);
                });
            } else {   
                oParentNode.$node
                    .nextAll(findPath + "[data-parent='" + oParentNode.id + "'][data-level='" + (oParentNode.level + 1) + "']")
                    .each(function () {
                        descendants.push(oParentNode.manager.getNode($(this)));
                    });
            }
            
            if (!isNaN(settings.index)) {
                var index = settings.index >= 0  ? settings.index - 1 : descendants.length + settings.index;
                return descendants[index];
            }
            return descendants;
        },        
        
        getMovePosition: function() {
            return this.movePosition;
        },
        
        setMovePosition: function(position, pointerOffset) {
            this.$node.removeClass(this.manager.options.classes.draggableContainer);
            if (position !== undefined) {
                this.$node.addClass(this.manager.options.classes.draggableContainer);
                this.movePosition = position;
                this.$pointer.css('top', pointerOffset.top + 'px');
                this.$pointer.css('left', pointerOffset.left + 'px');
            }
        },

        getId: function () {
            return this.id;
        },         
        
        getName: function () {
            return this.isEditable() ? this.$input.val() : this.name;
        },
        
        getParent: function () {
            return this.parent;
        },    
        
        getInsertPosition: function () {
            return this.insertPosition;
        },          
        
        getRelatedNodeId: function () {
            return this.relatedNodeId;
        },           
        
        init: function () {
            this.$node = this.manager.$nodeTemplate.clone(false);    
            this.$name = this.$node.find('.' + this.manager.options.classes.name);
            this.$ceIcon = this.$node.find('.' + this.manager.options.classes.ceIcon);
            this.$typeIcon = this.$node.find('.' + this.manager.options.classes.typeIcon);
            this.$icon = this.$node.find('.' + this.manager.options.classes.icon);
            this.$action = this.$node.find('.' + this.manager.options.classes.action);
            this.$indent = this.$node.find('.' + this.manager.options.classes.indent);
            this.$saveButton = this.$node.find('.' + this.manager.options.classes.saveButton);
            this.$cancelButton = this.$node.find('.' + this.manager.options.classes.cancelButton);      
            this.$input = this.$node.find('input');      
            this.$pointer = this.$node.find('.' + this.manager.options.classes.draggablePointer);
            
            this.render();
            this.attachEvents();
            
            this.$node.data('bs.gtreetable.gtreetablenode', this);
        },
        
        render: function() {
            this.$name.html(this.name);
            if (this.id !== undefined) {
                this.$node.attr('data-id', this.id);
                this.isSaved(true);
                
                if (this.manager.options.draggable === true) {
                    this.$node.addClass(this.manager.options.classes.draggable);
                }
            }
            this.$node.attr('data-parent', this.parent);
            this.$node.attr('data-level', this.level);

            this.$indent.css('marginLeft', ((parseInt(this.level) - this.manager.options.rootLevel) * this.manager.options.nodeIndent) + 'px').html('&zwnj;');
            
            if (this.type !== undefined && this.manager.options.types && this.manager.options.types[this.type] !== undefined) {
                this.$typeIcon.addClass(this.manager.options.types[this.type]).show();
            }
        },
        
        attachEvents: function () {
            var that = this,
                selectLimit = parseInt(this.manager.options.selectLimit);
            
            this.$node.mouseover(function () {
                if (!(that.manager.options.draggable === true && that.manager.isNodeDragging() === true)) {
                    that.$node.addClass(that.manager.options.classes.hovered);
                    that.isHovered(true);
                }
            });

            this.$node.mouseleave(function () {
                that.$node.removeClass(that.manager.options.classes.hovered);
                that.isHovered(false);
            });


            if (isNaN(selectLimit) === false && (selectLimit > 0 || selectLimit === -1) ) {
                this.$name.click(function (e) {
                    if (that.isSelected()) {
                        if ($.isFunction(that.manager.options.onUnselect)) {
                            that.manager.options.onUnselect(that);
                        }
                        that.isSelected(false);
                    } else {
                        var selectedNodes = that.manager.getSelectedNodes();
                        if (selectLimit === 1 && selectedNodes.length === 1) {
                            selectedNodes[0].isSelected(false);
                            selectedNodes = [];
                        } else if (selectedNodes.length === selectLimit) {
                            if ($.isFunction(that.manager.options.onSelectOverflow)) {
                                that.options.onSelectOverflow(that);
                            }
                            e.preventDefault();
                        }

                        if (selectedNodes.length < selectLimit || selectLimit === -1) {
                            that.isSelected(true);                            
                        }

                        if ($.isFunction(that.manager.options.onSelect)) {
                            that.manager.options.onSelect(that);
                        }
                    }
                });                
            } else {
                this.$name.click(function (e) { that.$ceIcon.click(); });
            }


            this.$ceIcon.click(function (e) {
                if (!that.isExpanded()) {
                    that.expand({
                        isAltPressed: e.altKey
                    });
                } else {
                    that.collapse();
                }
            });
            if (that.manager.options.dragCanExpand === true) {
                this.$ceIcon.mouseover(function (e) {
                    if (that.manager.options.draggable === true && that.manager.isNodeDragging() === true) {
                        if (!that.isExpanded()) {
                            that.expand();
                        }
                    }
                });
            }

            $.each(this.manager.actions, function (index, action) {
                that.$node.find('.' + that.manager.options.classes.action + '-' + index).click(function (event) {
                    action.event(that, that.manager);
                });
            });

            this.$saveButton.click(function () {
                that.save();
            });

            this.$cancelButton.click(function () {
                that.saveCancel();
            });
            
            if (that.manager.options.draggable === true) {
                var getMoveData = function (ui, $droppable) {
                    var draggableOffsetTop = ui.offset.top - $droppable.offset().top,
                        containerOffsetTop = $droppable.offset().top,
                        containerHeight = $droppable.outerHeight(),
                        containerWorkspace = containerHeight - Math.round(ui.helper.outerHeight() / 2),
                        movePosition,
                        pointerOffset = {left: that.manager.$tree.offset().left + 5 };

                    if (draggableOffsetTop  <= (containerWorkspace * 0.3)) {
                        movePosition = 'before'; 
                        pointerOffset.top = (containerOffsetTop + 3); 
                    } else if (draggableOffsetTop  <= (containerWorkspace * 0.7)) {
                        movePosition = 'lastChild';
                        pointerOffset.top = containerOffsetTop + (containerWorkspace / 2);
                    } else {
                        movePosition = 'after';
                        pointerOffset.top = containerOffsetTop + containerWorkspace;
                    }                    
                    pointerOffset.top += 2;
                    return {
                        position: movePosition,
                        pointerOffset: pointerOffset
                    };
                };
             
                this.$node
                    .draggable( {
                        scroll:true,
                        refreshPositions: that.manager.options.dragCanExpand,
                        helper: function (e) {
                            var oName = that.manager.getNode($(this));
                            return '<mark class="' + that.manager.options.classes.draggableHelper + '">' + oName.name + '</mark>';
                        },
                        cursorAt: {top:0, left: 0 },
                        handle: '.'+ that.manager.options.classes.handleIcon,
                        start: function (e) {
                            if (!$.browser.webkit) {
                                $(this).data("bs.gtreetable.gtreetablenode.scrollTop", $(window).scrollTop());
                            }
                        },
                        stop: function (e) {
                            that.manager.isNodeDragging(false);
                        },
                        drag: function (e, ui) {
                            if (!$.browser.webkit) {
                                var strollTop =  $(window).scrollTop(),
                                    delta = ($(this).data("bs.gtreetable.gtreetablenode.scrollTop") - strollTop);

                                ui.position.top -= strollTop + delta;
                                $(this).data("bs.gtreetable.gtreetablenode.startingScrollTop", strollTop);
                            }
                            var $droppable = $(this).data("bs.gtreetable.gtreetablenode.currentDroppable");
                            if ($droppable) {
                                var data = getMoveData(ui, $droppable);
                                that.manager.getNode($droppable).setMovePosition(data.position, data.pointerOffset);
                            }                            
                        }
                    })
                    .droppable({
                        accept: '.' + that.manager.options.classes.node,
                        over: function(event, ui) {
                            var $this = $(this),
                                data = getMoveData(ui, $this);
                            that.manager.getNode($this).setMovePosition(data.position, data.pointerOffset);
                            ui.draggable.data("bs.gtreetable.gtreetablenode.currentDroppable", $this);
                        },
                        out: function(event, ui) {
                            ui.draggable.removeData("bs.gtreetable.gtreetablenode.currentDroppable");
                            that.manager.getNode($(this)).setMovePosition();
                        },
                        drop: function(event, ui) {
                            var $this = $(this),
                                oNode = that.manager.getNode($this),
                                movePosition = oNode.getMovePosition();
                            ui.draggable.removeData("bs.gtreetable.gtreetablenode.currentDroppable");
                            oNode.setMovePosition();
                            that.manager.getNode(ui.draggable).move(oNode, movePosition);
                        }
                    });
            }             
        },
        
        makeEditable: function () {
            this.showForm(true);  
        }, 
        
        save: function () {
            var oNode = this;
            if ($.isFunction(oNode.manager.options.onSave)) {
                $.when($.ajax(oNode.manager.options.onSave(oNode))).done(function (data) {
                    oNode._save(data);
                });
            } else {
                oNode._save({
                    name: oNode.getName(),
                    id: oNode.manager.generateNewId()
                });
            }
        }, 
        
        _save: function(data) {
            var oNode = this;
            oNode.id = data.id;
            oNode.name = data.name;                                       

            if ($.isFunction(oNode.manager.options.sort)) {
                oNode.sort();
            }

            if (this.manager.options.cache > 0) {
                this.manager.cacheManager.synchronize(oNode.isSaved() ? 'edit' : 'add', oNode);
            }

            oNode.render(); 
            oNode.showForm(false);
            oNode.isHovered(false);
        },
        
        saveCancel: function () {
            this.showForm(false);
            if (!this.isSaved()) {
                this._remove();
            } 
        },

        expand: function (options) {
            var oNode = this, 
                    prevNode = oNode,
                settings = $.extend({}, {
                isAltPressed: false,
                onAfterFill: function (oNode, data) {
                    oNode.isExpanded(true);
                    if (data.length === 0) {
                        if (oNode.manager.options.showExpandIconOnEmpty === true) {
                            oNode.isExpanded(false);
                        } else {
                            oNode.showCeIcon(false);
                        }    
                    }
                }
            },options);

            $.when(this.manager.getSourceNodes(oNode.id, settings.isAltPressed)).done(function (result) {
                var data = result[oNode.manager.options.nodesWrapper];
                for(var x in data) {
                    var newNode = new GTreeTableNode(data[x], oNode.manager);
                    oNode.insertIntegral(newNode, prevNode);
                    prevNode = newNode;
                }

                if (settings && typeof $.isFunction(settings.onAfterFill)) {
                    settings.onAfterFill(oNode, data);
                }
            });            
        },
        
        collapse: function () {
            this.isExpanded(false);
            
            $.each(this.getDescendants({ depth: -1, includeNotSaved: true }), function () {
                this.$node.remove();
            });
        },        
        
        _canAdd: function(oNewNode) {
            var data = { result: !(oNewNode.parent === 0 && this.manager.options.manyroots === false) };
            if (!data.result) {
                data.message = this.manager.language.messages.onNewRootNotAllowed;
            }
            return data;
        },
        
        add: function (position, type) {
            var oTriggerNode = this,
                childPosition = (position === 'lastChild' || position === 'firstChild'),
                oNewNode = new GTreeTableNode({
                    level: oTriggerNode.level + (childPosition ? 1 : 0),
                    parent: oTriggerNode.level === this.manager.options.rootLevel && !childPosition ? 0 : (childPosition ? oTriggerNode.id : oTriggerNode.parent),
                    type: type
                },this.manager),
                canAddData = this._canAdd(oNewNode);
                
                
            if (!canAddData.result) {
                alert(canAddData.message);
                return false;
            }
           
            function ins() {
                if (childPosition) {
                    oTriggerNode.isExpanded(true);
                    oTriggerNode.showCeIcon(true);
                }
                oNewNode.insert(position, oTriggerNode);   
                oNewNode.insertPosition = position;
                oNewNode.relatedNodeId = oTriggerNode.id;                
                oNewNode.showForm(true);
            }
            
            if ( childPosition && !oTriggerNode.isExpanded() ) {
                oTriggerNode.expand({
                    onAfterFill: function () {
                        ins();
                    }
                });
            } else {
                ins();
            }
        },
        
        insert: function (position, oRelatedNode) {
            var oNode = this,
                oLastChild,
                oContext;
        
            if (position === 'before') {
                oRelatedNode.$node.before(oNode.$node);
            } else if (position === 'after') {
                oContext = oRelatedNode;
                if (oRelatedNode.isExpanded()) {
                    oLastChild = oRelatedNode.getDescendants({ depth: 1, index: -1, includeNotSaved: true });
                    oContext = oLastChild === undefined ? oContext : oLastChild;
                }
                oContext.$node.after(oNode.$node);
            } else if (position === 'firstChild') {
                this.manager.getNodeById(oRelatedNode.id).$node.after(oNode.$node);
            } else if (position === 'lastChild') {
                oLastChild = oRelatedNode.getDescendants({ depth: 1, index: -1, includeNotSaved: true });
                oContext = oLastChild === undefined ? oRelatedNode : oLastChild;
                oContext.$node.after(oNode.$node);
            } else {
                throw "Wrong position.";
            }
        },         
                
        insertIntegral: function (oNewNode, oNode) {
            if (oNode === undefined) {
                this.manager.$tree.append(oNewNode.$node);
            } else {
                oNode.$node.after(oNewNode.$node);
            }
        },           

        remove: function () {
            var oNode = this;

            if (oNode.isSaved() && $.isFunction(oNode.manager.options.onDelete)) {
                $.when($.ajax(oNode.manager.options.onDelete(oNode))).done(function () {
                    oNode._remove();
                });
            } else {
                this._remove();
            }
        },

        _remove: function () {            
            if (this.isExpanded() === true) {
                this.collapse(); 
            }
            this.$node.remove();            
            
            if (this.parent > 0) {
                var oParent = this.manager.getNodeById(this.parent);
                if (oParent.getDescendants({ depth: 1, includeNotSaved: true }).length === 0) {
                    oParent.collapse();
                }
            }
            
            if (this.manager.options.cache > 0) {
                this.manager.cacheManager.synchronize('delete', this);
            }
        },    
        
        _canMove: function(oDestination, position) {
            var oNode = this, 
                data = { result: true };
            if (oDestination.parent === 0 && this.manager.options.manyroots === false && position !== 'lastChild') {
                data.result = false;
                data.message = this.manager.language.messages.onMoveAsRoot;
            } else {              
                $.each(oDestination.getParents(), function () {
                    if (this.id === oNode.id) {
                        data.result = false;
                        data.message = this.manager.language.messages.onMoveInDescendant;   
                        return false;
                    }
                });          
            }
            return data;
        },
                
        move: function(oDestination, position) {            
            var oNode = this,
                moveData = this._canMove(oDestination, position);
            
            if (moveData.result === false) {
                alert(moveData.message);
                return false;
            }
            
            if ($.isFunction(oNode.manager.options.onMove)) {
                $.when($.ajax(oNode.manager.options.onMove(oNode, oDestination, position))).done(function (data) {
                    oNode._move(oDestination, position); 
                });
            } else {
                oNode._move(oDestination, position);
            }
        }, 
        
        _move: function(oDestination, position) {
            var oNode = this,
                oNodeDescendants = oNode.getDescendants({ depth: -1, includeNotSaved: true }),
                oOldNode = $.extend({}, oNode),
                oldIP = oNode.getIP(),
                delta = oDestination.level - oNode.level;

            oNode.parent = position === 'lastChild' ? oDestination.id : oDestination.parent;
            oNode.level = oDestination.level;

            if (position === 'lastChild' && !oDestination.isExpanded()) {
                oNode.$node.remove();
                $.each(oNodeDescendants, function () {
                    this.$node.remove();
                });                
            } else {

                if (position === 'lastChild') {
                    oNode.level += 1;
                    oDestination.showCeIcon(true);
                }
                oNode.render();
                oNode.insert(position, oDestination);

                if (oNodeDescendants.length > 0) {
                    var prevNode = oNode.$node;
                    if (position === 'lastChild') {
                        delta += 1;
                    }
                    $.each(oNodeDescendants, function() {
                        var oNode = this;
                        oNode.level += delta;
                        oNode.render();
                        prevNode.after(oNode.$node);
                        prevNode = oNode.$node;
                    });                
                }                        
            }

            // sprawdza, czy nie byl przeniesiony ostatni element
            // oOldSourceParent !== undefined => parent = 0
            var oOldNodeParent = oNode.manager.getNodeById(oOldNode.parent);
            if (oOldNodeParent !== undefined && oOldNodeParent.getDescendants({depth: 1, includeNotSaved: true}).length === 0) {
                oOldNodeParent.isExpanded(false);
            }

            if ($.isFunction(oNode.manager.options.sort)) {
                oNode.sort();
            }    
            
            if (this.manager.options.cache > 0) {
                this.manager.cacheManager.synchronize('move', oNode, { 'oOldNode': oOldNode, 'oldIP': oldIP });
            }            
        },        
        
        sort: function() {
            var oNode = this,
                oSiblings = oNode.getSiblings();

            // nie ma rodzenstwa = sortowanie nie jest potrzebne
            if (oSiblings.length > 0) {
                var oDescendants = !oNode.isExpanded() ? [] : oNode.getDescendants({ depth: -1, includeNotSaved: true }),
                    oRelated;
                
                $.each(oSiblings, function () {
                    if (oNode.manager.options.sort(oNode, this) === -1) {
                        oRelated = this;
                        return false;
                    }
                });
                
                if (oRelated === undefined) {
                    oRelated = oSiblings[oSiblings.length-1];
                    if (oRelated.isExpanded()) {
                        oRelated = oNode.manager.getNodeById(oNode.parent).getDescendants({ depth: -1, index: -1, includeNotSaved: true });
                    } 
                    oRelated.$node.after(oNode.$node);
                } else {
                    oRelated.$node.before(oNode.$node);
                }

                var prevNode = oNode.$node;
                $.each(oDescendants, function() {
                    var oCurrentNode = this;
                    prevNode.after(oCurrentNode.$node);
                    prevNode = oCurrentNode.$node;
                });                        
            }
        },        
        
        isLoading: function (action) {
            if (action === undefined) {
                return this._isLoading;
            } else if (action) {
                this.$name.addClass(this.manager.options.classes.loading);
                this._isLoading = true;
            } else {
                this.$name.removeClass(this.manager.options.classes.loading);
                this._isLoading = false;
            }
        },
        
        isSaved: function (action) {
            if (action === undefined) {
                return this._isSaved;
            } else if (action) {
                this.$node.addClass(this.manager.options.classes.saved);
                this._isSaved = true;
            } else {
                this.$node.removeClass(this.manager.options.classes.saved);
                this._isSaved = false;
            }
        },        
        
        isSelected: function (action) {
            if (action === undefined) {
                return this._isSelected;
            } else if (action) {
                this.$node.addClass(this.manager.options.classes.selected);
                this._isSelected = true;
            } else {
                this.$node.removeClass(this.manager.options.classes.selected);
                this._isSelected = false;
            }            
        },
        
        isExpanded: function (action) {
            if (action === undefined) {
                return this._isExpanded;
            } else if (action) {
                this.$node.addClass(this.manager.options.classes.expanded).removeClass(this.manager.options.classes.collapsed);
                this._isExpanded = true;
            } else {
                this.$node.addClass(this.manager.options.classes.collapsed).removeClass(this.manager.options.classes.expanded);
                this._isExpanded = false;
            }            
        },     
        
        isHovered: function (action) {
            if (action === undefined) {
                return this._isHovered;
            } else if (action) {
                this.$node.addClass(this.manager.options.classes.hovered);
                this._isHovered = true;
            } else {
                this.$node.removeClass(this.manager.options.classes.hovered);
                this.$node.find('.btn-group').removeClass('open');
                this._isHovered = false;
            }            
        },
        
        isEditable: function (action) {
            if (action === undefined) {
                return this._isEditable;
            } else {
                this._isEditable = action;
            }   
        },        
        
        showCeIcon: function (action) {
            this.$ceIcon.css('visibility', action ? 'visible' : 'hidden');
        },
        
        showForm: function (action) {
            if (action === true) {
                this.isEditable(true);
                this.$input.val(this.name);
                this.$name.addClass('hide');
                this.$action.removeClass('hide');
                //TODO nie dziala zawsze
                this.$input.focus();
            } else {
                this.isEditable(false);
                this.$name.removeClass('hide');
                this.$action.addClass('hide');
            }
        }
    };
    
   function GTreeTableCache(manager) {
        this._cached = {};
        this.manager = manager;
    }
    
    GTreeTableCache.prototype = {  
        _getIP: function (param) {
            return typeof param === "string" ? param : param.getIP();
        },
        
        get: function(param) {
            return this._cached[this._getIP(param)];
        },
        
        set: function (param, data) {
            this._cached[this._getIP(param)] = data;
        },
                
        remove: function (param) {
            this._cached[this._getIP(param)] = undefined;
        },
        
        synchronize: function (method, oNode, params) {
            if (oNode.parent > 0) {
                switch (method) {
                    case 'add':
                        this._synchronizeAdd(oNode);
                        break;
                        
                    case 'edit': 
                        this._synchronizeEdit(oNode);
                        break;
                        
                    case 'delete':
                        this._synchronizeDelete(oNode);
                        break;
                        
                    case 'move':
                        this._synchronizeMove(oNode, params);
                        break;
                        
                    default:
                        throw "Wrong method.";
                }
            }            
        },
        
        _synchronizeAdd: function (oNode) {
            var oParentNode = this.manager.getNodeById(oNode.parent);

            if (this.manager.options.cache > 1) {
                var data = this.get(oParentNode);
                if (data !== undefined) {
                    data.push({
                        id: oNode.id,
                        name: oNode.getName(),
                        level: oNode.level,
                        type: oNode.type,
                        parent: oNode.parent
                    });
                    this.set(oParentNode, this.isSortDefined() ? this.sort(data) : data);
                }
            } else {
                this.remove(oParentNode);
            }
        },
        
        _synchronizeEdit: function (oNode) {
            var oParentNode = this.manager.getNodeById(oNode.parent);
            
            if (this.manager.options.cache > 1) {
                var data = this.get(oParentNode);
                $.each(data, function () {
                    if (this.id === oNode.id) {
                        this.name = oNode.getName();
                        return false;
                    }
                });
                this.set(oParentNode, this.isSortDefined() ? this.sort(data) : data);
            } else {
                this.remove(oParentNode);
            }            
        },
        
        _synchronizeDelete: function(oNode) {            
            var oParentNode = this.manager.getNodeById(oNode.parent);
            
            if (this.manager.options.cache > 1) {
                var data = this.get(oParentNode),
                    position;
                
                // pobieranie pozycji
                $.each(data, function(index) {
                    if (this.id === oNode.id) {
                        position = index;
                        return false;
                    }
                });
                if (position !== undefined) {
                    data.splice(position, 1);
                    this.set(oParentNode, data);
                }
            } else {
                this.remove(oParentNode);
            }                      
        },
        
        _synchronizeMove: function(oNode, params) {
            var that = this,
                newIP = oNode.getIP(),
                delta =  oNode.level - params.oOldNode.level;
        
            $.each(this._cached, function (index) {
                if (index === params.oldIP || index.indexOf(params.oldIP+'.') === 0) {
 
                    if (that.manager.options.cache > 1) {
                        var newData = [],
                            newIndex = index !== params.oldIP ? newIP + index.substr(params.oldIP.length) : newIP;
                        
                        $(that.get(index)).each(function () {
                            this.level += delta;
                            newData.push(this);
                        });      
                        that.set(newIndex, newData);
                    } 
                    
                    that.remove(index);
                                        
                }
            });
            this.synchronize('delete', params.oOldNode);   
            this.synchronize('add', oNode);            
        },
        
        isSortDefined: function () {
            return $.isFunction(this.manager.options.sort);
        },
        
        sort: function (data) {
            return data.sort(this.manager.options.sort);
        }
    };    

    // OVERLAYINPUT PLUGIN DEFINITION
    // ==============================

    function Plugin(option, _relatedTarget) {
        var retval = null;

        this.each(function () {
            var $this = $(this),
                data = $this.data('bs.gtreetable'),
                options = $.extend({}, $.fn.gtreetable.defaults, $this.data(), typeof option === 'object' && option);

            if (!data) {
                data = new GTreeTable(this, options);
                $this.data('bs.gtreetable', data);
            }

            if (typeof option === 'string') {
                retval = data[option](_relatedTarget);
            }
        });

        if (!retval) {
            retval = this;
        }

        return retval;
    }

    var old = $.fn.gtreetable;

    $.fn.gtreetable = Plugin;
    $.fn.gtreetable.Constructor = GTreeTable;

    $.fn.gtreetable.defaults = {
        nodesWrapper: 'nodes',
        nodeIndent: 16,
        language: 'en',
        inputWidth: '60%',
        cache: 2,
        readonly: false,
        selectLimit: 1,
        rootLevel: 0,        
        manyroots: false,
        draggable: false,
        dragCanExpand: false,
        showExpandIconOnEmpty: false,        
        languages: {
            'en-US': {
                save: 'Save',
                cancel: 'Cancel',
                action: 'Action',
                actions: {
                    createBefore: 'Create before',
                    createAfter: 'Create after',
                    createFirstChild: 'Create first child',
                    createLastChild: 'Create last child',
                    update: 'Update',
                    'delete': 'Delete'
                },
                messages: {
                    onDelete: 'Are you sure?',
                    onNewRootNotAllowed: 'Adding the now node as root is not allowed.',
                    onMoveInDescendant: 'The target node should not be descendant.',
                    onMoveAsRoot: 'The target node should not be root.'
                }                
            }
        },
        defaultActions: [
            {
                name: '${createBefore}',
                event: function (oNode, oManager) {
                    oNode.add('before', 'default');
                }
            },
            {
                name: '${createAfter}',
                event: function (oNode, oManager) {
                    oNode.add('after', 'default');
                }
            },
            {
                name: '${createFirstChild}',
                event: function (oNode, oManager) {
                    oNode.add('firstChild', 'default');
                }
            },
            {
                name: '${createLastChild}',
                event: function (oNode, oManager) {
                    oNode.add('lastChild', 'default');
                }
            },
            {
                divider: true
            },
            {
                name: '${update}',
                event: function (oNode, oManager) {
                    oNode.makeEditable();
                }
            },
            {
                name: '${delete}',
                event: function (oNode, oManager) {
                    if (confirm(oManager.language.messages.onDelete)) {
                        oNode.remove();
                    }
                }
            }
        ],
        classes: {
            node: 'node',
            loading: 'node-loading',
            selected: 'node-selected',
            hovered: 'node-hovered',
            expanded: 'node-expanded',
            collapsed : 'node-collapsed',
            draggable : 'node-draggable',
            draggableHelper : 'node-draggable-helper',
            draggablePointer : 'node-draggable-pointer',
            draggableContainer : 'node-draggable-container',
            saved: 'node-saved',
            name: 'node-name',
            icon: 'node-icon',            
            selectedIcon: 'node-icon-selected',
            ceIcon: 'node-icon-ce',
            typeIcon: 'node-icon-type',
            handleIcon : 'node-icon-handle',
            action: 'node-action',
            indent: 'node-indent',
            saveButton: 'node-save',
            cancelButton: 'node-cancel',
            buttons: 'node-buttons'            
        }
    };

    // OVERLAYINPUT NO CONFLICT
    // ========================

    $.fn.gtreetable.noConflict = function () {
        $.fn.gtreetable = old;
        return this;
    };

}(jQuery));
