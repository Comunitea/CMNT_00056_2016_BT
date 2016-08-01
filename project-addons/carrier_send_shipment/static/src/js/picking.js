openerp.carrier_send_shipment = function(instance){
    instance.stock.PickingEditorWidget.include({

        renderElement: function(){
            var self = this
            this._super();
            this.$('.js_shipment_print').click(function(){
                    var $ship_modal = self.$el.siblings('#js_SendCarrier');
                    //disconnect scanner to prevent scanning a product in the back while dialog is open
                    self.getParent().barcode_scanner.disconnect();
                    $ship_modal.modal()
                    //focus input
                    $ship_modal.on('shown.bs.modal', function(){
                        var picking = self.getParent().picking
                        self.$('.js_weight_edit').focus();
                        self.$('.js_weight_edit').val(picking.weight_edit);
                        self.$('.js_asm_return').val(picking.asm_return);
                        self.$('.js_number_of_packages').val(picking.number_of_packages);
                        self.$('.js_carrier_notes').val(picking.carrier_notes || '');

                    })
                    //reactivate scanner when dialog close
                    $ship_modal.on('hidden.bs.modal', function(){
                        self.getParent().barcode_scanner.connect(function(ean){
                            self.getParent().scan(ean);
                        });
                    })
                    self.$('.js_weight_edit').focus();
                    //button action
                    self.$('.js_send_shipment').click(function(){
                        data = {}
                        data.weight_edit = self.$('.js_weight_edit').val()
                        data.asm_return = self.$('.js_asm_return').val()
                        data.number_of_packages = self.$('.js_number_of_packages').val()
                        data.carrier_notes = self.$('.js_carrier_notes').val()
                        picking_obj = new instance.web.Model('stock.picking')
                        picking_obj.call('write',[[ self.getParent().picking.id], data]).then(function(wr){
                            picking_obj.call('barcode_send_shipment', [[ self.getParent().picking.id]]).then(function(sended){
                               console.log(sended)
                            });

                        });

                        $ship_modal.modal('hide');
                        //we need this here since it is not sure the hide event
                        //will be catch because we refresh the view after the create_lot call
                        self.getParent().barcode_scanner.connect(function(ean){
                            self.getParent().scan(ean);
                        });
                    });
                });

        },

        });
};
