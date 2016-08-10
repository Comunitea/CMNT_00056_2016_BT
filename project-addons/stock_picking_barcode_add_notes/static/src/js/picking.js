openerp.stock_picking_barcode_add_notes = function(instance){
    instance.stock.PickingEditorWidget.include({

        renderElement: function(){
            var self = this
            this._super();
            this.$('.js_picking_note').val(this.getParent().picking.note);
            this.$('.js_picking_note').focusout(function(){
                if(self.getParent().picking.note !== self.$('.js_picking_note').val()){
                    var note_val = self.$('.js_picking_note').val();
                    data = {
                        note: note_val
                    }
                    self.getParent().picking.note = note_val
                    picking_obj = new instance.web.Model('stock.picking');
                    picking_obj.call('write',[[ self.getParent().picking.id], data]);
                }
            });
        },

    });
};
