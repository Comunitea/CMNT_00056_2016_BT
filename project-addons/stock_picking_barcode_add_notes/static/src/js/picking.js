openerp.stock_picking_barcode_add_notes = function(instance){
    instance.stock.PickingEditorWidget.include({

        renderElement: function(){
            var self = this
            this._super();
            picking_obj = new instance.web.Model('stock.picking');
            this.$('.js_picking_note').val(this.getParent().picking.note);
            this.$('.js_invoice_print').click(function(){
                return picking_obj.call('do_print_invoice',[[self.getParent().picking.id]])
                           .then(function(action){
                               if(action != null){
                                    return self.do_action(action);
                                }
                           });
            });
            this.$('.js_picking_note').focusout(function(){
                if(self.getParent().picking.note !== self.$('.js_picking_note').val()){
                    var note_val = self.$('.js_picking_note').val();
                    data = {
                        note: note_val
                    }
                    self.getParent().picking.note = note_val
                    picking_obj.call('write',[[ self.getParent().picking.id], data]);
                }
            });
        },

    });

    instance.stock.PickingMainWidget.include({
        get_header: function(){
            var name = this._super();
            if(this.picking){
                return name.concat(' - ', this.picking.partner_id[1]);
            }else{
                return '';
            }
        }
    });
};
