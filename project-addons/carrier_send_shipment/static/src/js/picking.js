openerp.carrier_send_shipment = function(instance){
    var _t = instance.web._t;
    instance.stock.PickingEditorWidget.include({

        hide_shipment_fields: function(){
            // Se ocultan los div que contienen los label e input.
            this.$('.js_weight_edit').parent().hide();
            this.$('.js_number_of_packages').parent().hide();
            this.$('.js_carrier_notes').parent().hide();
        },

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
                        if(picking.carrier_delivery){
                            self.hide_shipment_fields()
                            self.$('.js_send_shipment').text(_t('Print label'))
                        }
                        else{
                            self.$('.js_weight_edit').val(picking.weight_edit);
                            self.$('.js_number_of_packages').val(picking.number_of_packages);
                            self.$('.js_carrier_notes').val(picking.carrier_notes || '');
                        }

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
                        self.$('.js_send_shipment').prop('disabled', true);
                        data = {}
                        if(!self.getParent().picking.carrier_delivery){
                            data.weight_edit = self.$('.js_weight_edit').val()
                            data.number_of_packages = self.$('.js_number_of_packages').val()
                            data.carrier_notes = self.$('.js_carrier_notes').val()
                        }
                        picking_obj = new instance.web.Model('stock.picking')
                        picking_obj.call('write',[[ self.getParent().picking.id], data]).then(function(wr){
                            picking_obj.call('barcode_send_shipment', [[ self.getParent().picking.id]]).then(function(label){
                                self.hide_shipment_fields()
                                self.$('.js_send_shipment').hide()
                                var download_link = $('<a/>')
                                download_link.attr('href', 'data:application/pdf;base64,'.concat(label))
                                download_link.attr('download', '')
                                download_link.text(_t('Click to download'))
                                download_link.click(function(){$ship_modal.modal('hide');})
                               $('.js_send_shipment').parent().append(download_link)
                            });

                        });

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
