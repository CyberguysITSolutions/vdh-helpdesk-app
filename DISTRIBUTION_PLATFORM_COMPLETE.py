# DISTRIBUTION PLATFORM - COMPLETE IMPLEMENTATION
# Add this to Resource Management section in helpdesk_app.py
# Location: Inside "if page == '📦 Resource Management':" section

# =============================================================================
# DISTRIBUTION PLATFORM TAB
# =============================================================================

with tab3:  # Distribution Platform tab
    st.subheader("📱 Distribution Platform")
    st.markdown("Scan items and register recipients during resource distribution events")
    
    # Check if distribution tables exist
    dist_check_query = "SELECT COUNT(*) as count FROM sys.tables WHERE name = 'distributions'"
    dist_check_df, dist_check_err = execute_query(dist_check_query)
    
    if dist_check_err or (dist_check_df is not None and dist_check_df.iloc[0]['count'] == 0):
        st.warning("⚠️ Distribution platform tables not found. Please run the database schema setup.")
        st.stop()
    
    # Initialize session state
    if 'active_distribution' not in st.session_state:
        st.session_state.active_distribution = None
    if 'current_recipient' not in st.session_state:
        st.session_state.current_recipient = None
    if 'distribution_stats' not in st.session_state:
        st.session_state.distribution_stats = {'items': 0, 'recipients': 0, 'raffles': 0}
    
    # =========================================================================
    # NO ACTIVE DISTRIBUTION - SHOW START SCREEN
    # =========================================================================
    
    if st.session_state.active_distribution is None:
        st.info("👆 Select a manifest and start a distribution session to begin scanning items")
        
        # Get popup/event manifests only
        manifest_query = """
            SELECT 
                manifest_id,
                manifest_name,
                manifest_type,
                location,
                status,
                created_at
            FROM dbo.resource_manifests
            WHERE manifest_type = 'Popup/Event'
            AND is_active = 1
            AND status = 'Active'
            ORDER BY created_at DESC
        """
        
        manifest_df, manifest_err = execute_query(manifest_query)
        
        if manifest_err:
            st.error(f"Error loading manifests: {manifest_err}")
        elif manifest_df is None or len(manifest_df) == 0:
            st.warning("No active popup/event manifests found. Create a popup/event manifest first.")
        else:
            # Manifest selection form
            with st.form("start_distribution_form"):
                st.markdown("### Start New Distribution Session")
                
                manifest_options = [
                    f"{row['manifest_name']} - {row['location']}" 
                    for _, row in manifest_df.iterrows()
                ]
                selected_manifest = st.selectbox(
                    "Select Manifest",
                    options=manifest_options,
                    help="Only popup/event type manifests are shown"
                )
                
                distribution_name = st.text_input(
                    "Distribution Name",
                    value=f"Distribution - {datetime.now().strftime('%Y-%m-%d')}",
                    help="Optional: Give this distribution session a name"
                )
                
                notes = st.text_area(
                    "Notes (Optional)",
                    placeholder="Add any notes about this distribution session..."
                )
                
                start_button = st.form_submit_button("🚀 Start Distribution Session", type="primary")
                
                if start_button:
                    # Get selected manifest ID
                    selected_idx = manifest_options.index(selected_manifest)
                    manifest_id = manifest_df.iloc[selected_idx]['manifest_id']
                    manifest_location = manifest_df.iloc[selected_idx]['location']
                    
                    # Create distribution session
                    username = st.session_state.get('username', 'Unknown')
                    
                    create_dist_query = """
                        INSERT INTO dbo.distributions (
                            manifest_id, distribution_name, location, 
                            distributed_by, notes, status
                        )
                        VALUES (?, ?, ?, ?, ?, 'Active');
                        SELECT SCOPE_IDENTITY() as distribution_id;
                    """
                    
                    result_df, create_err = execute_query(
                        create_dist_query,
                        params=(manifest_id, distribution_name, manifest_location, 
                               username, notes)
                    )
                    
                    if create_err:
                        st.error(f"Error creating distribution session: {create_err}")
                    else:
                        distribution_id = int(result_df.iloc[0]['distribution_id'])
                        st.session_state.active_distribution = {
                            'distribution_id': distribution_id,
                            'manifest_id': manifest_id,
                            'distribution_name': distribution_name,
                            'location': manifest_location
                        }
                        st.session_state.distribution_stats = {'items': 0, 'recipients': 0, 'raffles': 0}
                        st.success(f"✅ Distribution session started: {distribution_name}")
                        st.rerun()
    
    # =========================================================================
    # ACTIVE DISTRIBUTION - SHOW SCANNING INTERFACE
    # =========================================================================
    
    else:
        dist_info = st.session_state.active_distribution
        
        # Header with session info
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"### 🔴 LIVE: {dist_info['distribution_name']}")
            st.caption(f"📍 {dist_info['location']} | Manifest ID: {dist_info['manifest_id']}")
        with col2:
            if st.button("👥 New Recipient", use_container_width=True):
                st.session_state.current_recipient = None
        with col3:
            if st.button("🛑 End Session", type="secondary", use_container_width=True):
                # End distribution session
                end_query = """
                    UPDATE dbo.distributions 
                    SET status = 'Completed', end_time = GETDATE()
                    WHERE distribution_id = ?
                """
                _, end_err = execute_query(end_query, params=(dist_info['distribution_id'],))
                
                if not end_err:
                    st.success("✅ Distribution session ended")
                    st.session_state.active_distribution = None
                    st.session_state.current_recipient = None
                    st.rerun()
        
        st.markdown("---")
        
        # Session stats
        stats_col1, stats_col2, stats_col3 = st.columns(3)
        with stats_col1:
            st.metric("Items Distributed", st.session_state.distribution_stats['items'])
        with stats_col2:
            st.metric("Recipients Served", st.session_state.distribution_stats['recipients'])
        with stats_col3:
            st.metric("Raffle Entries", st.session_state.distribution_stats['raffles'])
        
        st.markdown("---")
        
        # =====================================================================
        # RECIPIENT REGISTRATION
        # =====================================================================
        
        if st.session_state.current_recipient is None:
            st.info("👤 Register a recipient to start scanning items")
            
            with st.form("register_recipient_form"):
                st.markdown("### Register New Recipient")
                
                recipient_name = st.text_input("Name *", placeholder="Enter recipient's name")
                
                col1, col2 = st.columns(2)
                with col1:
                    email = st.text_input("Email (Optional)", placeholder="recipient@email.com")
                with col2:
                    phone = st.text_input("Phone (Optional)", placeholder="(555) 123-4567")
                
                opt_in_raffles = st.checkbox("✓ Opt-in to future raffles", value=True)
                opt_in_communications = st.checkbox("✓ Receive VDH communications")
                
                register_button = st.form_submit_button("Register & Start Scanning", type="primary")
                
                if register_button:
                    if not recipient_name.strip():
                        st.error("❌ Recipient name is required")
                    else:
                        # Create recipient
                        create_recipient_query = """
                            INSERT INTO dbo.distribution_recipients (
                                distribution_id, recipient_name, email, phone,
                                opt_in_raffles, opt_in_communications
                            )
                            VALUES (?, ?, ?, ?, ?, ?);
                            SELECT SCOPE_IDENTITY() as recipient_id;
                        """
                        
                        recipient_df, recipient_err = execute_query(
                            create_recipient_query,
                            params=(
                                dist_info['distribution_id'],
                                recipient_name.strip(),
                                email.strip() if email else None,
                                phone.strip() if phone else None,
                                1 if opt_in_raffles else 0,
                                1 if opt_in_communications else 0
                            )
                        )
                        
                        if recipient_err:
                            st.error(f"Error registering recipient: {recipient_err}")
                        else:
                            recipient_id = int(recipient_df.iloc[0]['recipient_id'])
                            st.session_state.current_recipient = {
                                'recipient_id': recipient_id,
                                'name': recipient_name.strip(),
                                'items_received': 0
                            }
                            st.session_state.distribution_stats['recipients'] += 1
                            if opt_in_raffles:
                                st.session_state.distribution_stats['raffles'] += 1
                            st.success(f"✅ Registered: {recipient_name}")
                            st.rerun()
        
        # =====================================================================
        # BARCODE SCANNING INTERFACE
        # =====================================================================
        
        else:
            recipient_info = st.session_state.current_recipient
            
            # Current recipient banner
            st.success(f"👤 Current Recipient: **{recipient_info['name']}** | Items Received: {recipient_info['items_received']}")
            
            # Get available items from manifest
            items_query = """
                SELECT 
                    item_id,
                    item_name,
                    category,
                    quantity_received,
                    barcode
                FROM dbo.manifest_items
                WHERE manifest_id = ?
                ORDER BY item_name
            """
            
            items_df, items_err = execute_query(items_query, params=(dist_info['manifest_id'],))
            
            if items_err:
                st.error(f"Error loading items: {items_err}")
            elif items_df is None or len(items_df) == 0:
                st.warning("No items found in this manifest")
            else:
                # Barcode scanning interface
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("### 🔍 Scan Item")
                    barcode_input = st.text_input(
                        "Barcode",
                        placeholder="Scan barcode or type manually...",
                        key="barcode_input",
                        label_visibility="collapsed"
                    )
                    
                    if barcode_input:
                        # Find item by barcode
                        matching_items = items_df[items_df['barcode'] == barcode_input]
                        
                        if len(matching_items) == 0:
                            st.error(f"❌ Barcode not found: {barcode_input}")
                        else:
                            item = matching_items.iloc[0]
                            
                            # Record distribution
                            record_query = """
                                INSERT INTO dbo.distribution_items (
                                    distribution_id, manifest_item_id, item_name,
                                    barcode, quantity_distributed, scanned_by, recipient_id
                                )
                                VALUES (?, ?, ?, ?, 1, ?, ?)
                            """
                            
                            username = st.session_state.get('username', 'Unknown')
                            _, record_err = execute_query(
                                record_query,
                                params=(
                                    dist_info['distribution_id'],
                                    int(item['item_id']),
                                    item['item_name'],
                                    barcode_input,
                                    username,
                                    recipient_info['recipient_id']
                                )
                            )
                            
                            if not record_err:
                                st.success(f"✅ Distributed: {item['item_name']}")
                                st.session_state.current_recipient['items_received'] += 1
                                st.session_state.distribution_stats['items'] += 1
                                st.rerun()
                
                with col2:
                    st.markdown("### Manual Selection")
                    item_options = [f"{row['item_name']}" for _, row in items_df.iterrows()]
                    selected_item = st.selectbox(
                        "Or select item",
                        options=[""] + item_options,
                        label_visibility="collapsed"
                    )
                    
                    if selected_item and st.button("Add Item", use_container_width=True):
                        # Get selected item
                        item = items_df[items_df['item_name'] == selected_item].iloc[0]
                        
                        # Record distribution
                        record_query = """
                            INSERT INTO dbo.distribution_items (
                                distribution_id, manifest_item_id, item_name,
                                quantity_distributed, scanned_by, recipient_id
                            )
                            VALUES (?, ?, ?, 1, ?, ?)
                        """
                        
                        username = st.session_state.get('username', 'Unknown')
                        _, record_err = execute_query(
                            record_query,
                            params=(
                                dist_info['distribution_id'],
                                int(item['item_id']),
                                item['item_name'],
                                username,
                                recipient_info['recipient_id']
                            )
                        )
                        
                        if not record_err:
                            st.success(f"✅ Distributed: {item['item_name']}")
                            st.session_state.current_recipient['items_received'] += 1
                            st.session_state.distribution_stats['items'] += 1
                            st.rerun()
                
                # Items distributed to current recipient
                st.markdown("---")
                st.markdown("### Items Given to This Recipient")
                
                recipient_items_query = """
                    SELECT 
                        item_name,
                        quantity_distributed,
                        scanned_at
                    FROM dbo.distribution_items
                    WHERE distribution_id = ? AND recipient_id = ?
                    ORDER BY scanned_at DESC
                """
                
                recipient_items_df, rec_items_err = execute_query(
                    recipient_items_query,
                    params=(dist_info['distribution_id'], recipient_info['recipient_id'])
                )
                
                if not rec_items_err and recipient_items_df is not None and len(recipient_items_df) > 0:
                    st.dataframe(recipient_items_df, use_container_width=True)
                else:
                    st.info("No items distributed to this recipient yet")
