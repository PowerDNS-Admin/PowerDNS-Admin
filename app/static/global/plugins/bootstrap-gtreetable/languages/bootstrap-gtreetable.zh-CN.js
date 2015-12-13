/* ========================================================= 
 * bootstrap-gtreetable v2.2.1-alpha
 * https://github.com/gilek/bootstrap-gtreetable
 * ========================================================= 
 * Copyright 2014 Maciej Kłak
 * Licensed under MIT (https://github.com/gilek/bootstrap-gtreetable/blob/master/LICENSE)
 * ========================================================= */

// Chinese Translation by Thinking Song

(function( $ ) {
    $.fn.gtreetable.defaults.languages['zh-CN'] = {
        save: '保存',
        cancel: '取消',
        action: '操作',
        actions: {
            createBefore: '之前创建',
            createAfter: '之后创建',
            createFirstChild: '创建第一个子节点',
            createLastChild: '创建最后一个子节点',
            update: '更新',
            'delete': '上传'
        },
        messages: {
            onDelete: '你确定删除?',
            onNewRootNotAllowed: '不允许添加新的根节点.',
            onMoveInDescendant: '目标节点不能是后裔节点T.',
            onMoveAsRoot: '目标节点不能是根节点.'
        }
    };
}( jQuery ));
