/* ========================================================= 
 * bootstrap-gtreetable v2.2.1-alpha
 * https://github.com/gilek/bootstrap-gtreetable
 * ========================================================= 
 * Copyright 2014 Maciej Kłak
 * Licensed under MIT (https://github.com/gilek/bootstrap-gtreetable/blob/master/LICENSE)
 * ========================================================= */

/* ========================================================= 
 * Russian translation by Dunaevsky Maxim
 * ========================================================= */

(function ($) {
    $.fn.gtreetable.defaults.languages.ru = {
        save: 'Сохранить',
        cancel: 'Отмена',
        action: 'Действие',
        actions: {
            createBefore: 'Вставить до',
            createAfter: 'Вставить после',
            createFirstChild: 'Создать первого потомка',
            createLastChild: 'Создать последнего потомка',
            update: 'Обновить',
            'delete': 'Удалить'
        },
        messages: {
            onDelete: 'Вы уверены?',
            onNewRootNotAllowed: 'Создание новых узлов в корне запрещено.',
            onMoveInDescendant: 'Целевой узел не может быть потомком.',
            onMoveAsRoot: 'Целевой узел не может быть корневым.'
        }                
    };
}(jQuery));