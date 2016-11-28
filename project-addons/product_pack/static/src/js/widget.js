openerp.product_pack = function(instance){
    var _t = instance.web._t;
    instance.stock.PickingMainWidget.include({

        scan: function(ean){ //scans a barcode, sends it to the server, then reload the ui
                var self = this;
                var product_visible_ids = this.picking_editor.get_visible_ids();
                return new instance.web.Model('stock.picking')
                    .call('process_barcode_from_ui', [self.picking.id, ean, product_visible_ids])
                    .then(function(result){
                        if (result.filter_loc !== false){
                            //check if we have receive a location as answer
                            if (result.filter_loc !== undefined){
                                var modal_loc_hidden = self.$('#js_LocationChooseModal').attr('aria-hidden');
                                if (modal_loc_hidden === "false"){
                                    var line = self.$('#js_LocationChooseModal .js_loc_option[data-loc-id='+result.filter_loc_id+']').attr('selected','selected');
                                }
                                else{
                                    self.$('.oe_searchbox').val(result.filter_loc);
                                    self.on_searchbox(result.filter_loc);
                                }
                            }
                        }
                        if (result.operation_id !== false){
                            self.refresh_ui(self.picking.id).then(function(){
                                    Array.from(result.operation_id).forEach(function(entry) {
                                        self.picking_editor.blink(entry);
                                    });
                            });
                        }
                    });
            },
    });
};
