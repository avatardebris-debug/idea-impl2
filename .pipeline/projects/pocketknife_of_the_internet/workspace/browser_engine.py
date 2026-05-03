
    def detach_tab_to_window(self, window_id: int) -> Optional[Dict[str, Any]]:
        """
        Detach a tab from its current window and create a new floating window.
        Returns transition metadata for animation, or None if invalid.
        """
        if window_id not in self.tab_registry:
            return None

        tab = self.tab_registry[window_id]
        if tab.is_detached:
            return None

        # Get current window position for transition start
        current_window = self.window_manager.windows.get(window_id)
        start_x = current_window.x if current_window else 0
        start_y = current_window.y if current_window else 0

        # Create new floating window
        new_window_id = self.window_manager.create_floating_window(
            x=start_x + 50,  # Offset for visual effect
            y=start_y + 50,
            width=current_window.width if current_window else 800,
            height=current_window.height if current_window else 600
        )

        # Create new detached tab
        detached_tab = Tab(
            window_id=new_window_id,
            url=tab.url,
            title=tab.title,
            is_detached=True
        )
        detached_tab.history = list(tab.history)
        detached_tab.history_index = tab.history_index

        # Remove old tab, add new detached tab
        del self.tab_registry[window_id]
        self.tab_registry[new_window_id] = detached_tab

        # Update window URL to match tab
        self.window_manager.windows[new_window_id].url = tab.url

        # Calculate transition end position (center of screen)
        screen_width = self.window_manager.screen_width
        screen_height = self.window_manager.screen_height
        end_x = (screen_width - detached_tab.window_id) // 2
        end_y = (screen_height - detached_tab.window_id) // 2

        return {
            "detached_window_id": new_window_id,
            "transition": {
                "start_x": start_x,
                "start_y": start_y,
                "end_x": end_x,
                "end_y": end_y,
                "duration_ms": 300,
                "easing_type": "ease_out_cubic"
            }
        }

    def reattach_window_to_tab(self, window_id: int) -> Optional[Dict[str, Any]]:
        """
        Reattach a floating window back to the main tab layout.
        Returns transition metadata for animation, or None if invalid.
        """
        if window_id not in self.tab_registry:
            return None

        tab = self.tab_registry[window_id]
        if not tab.is_detached:
            return None

        # Get current floating window position
        current_window = self.window_manager.windows.get(window_id)
        start_x = current_window.x if current_window else 0
        start_y = current_window.y if current_window else 0

        # Reattach to main layout
        self.window_manager.reattach_window(window_id)

        # Update tab state
        tab.is_detached = False

        # Calculate transition end position (main layout area)
        main_layout = self.window_manager.get_main_layout_area()
        end_x = main_layout.x
        end_y = main_layout.y

        return {
            "reattached_window_id": window_id,
            "transition": {
                "start_x": start_x,
                "start_y": start_y,
                "end_x": end_x,
                "end_y": end_y,
                "duration_ms": 300,
                "easing_type": "ease_in_cubic"
            }
        }