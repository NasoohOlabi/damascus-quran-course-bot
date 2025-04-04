# Conversation Flow Chart

This document provides a visual representation of the conversation flow in the Makin Damascus Bot. The diagram illustrates the three-level nested `ConversationHandler` structure described in the [Conversation Flow Documentation](CONVERSATION_FLOW.md).

## Understanding the Flow Chart

### Color Coding

The flow chart uses color coding to distinguish between different conversation levels:

- **Blue**: Top-level conversation handler (main menu and action selection)
- **Green**: Second-level conversation handler (family member type selection)
- **Orange**: Third-level conversation handler (feature collection)
- **Gray**: Meta states (stopping, end states)
- **Red**: End state

### State Transitions

Arrows in the diagram represent state transitions:

- **Solid arrows**: Direct transitions within the same conversation level
- **Dashed arrows**: Transitions between different conversation levels
- **Dotted arrows**: State mappings between parent and child handlers

### Key Components

1. **Top Level Conversation Handler**
   - Entry point: `/start` command
   - Main states: SELECTING_ACTION, SHOWING, DESCRIBING_SELF
   - Manages the overall conversation flow

2. **Second Level Conversation Handler (add_member_conv)**
   - Entry point: "Add family member" selection
   - States: ADDING_MEMBER, SELECTING_LEVEL, SELECTING_GENDER
   - Handles the process of adding a family member

3. **Third Level Conversation Handler (description_conv)**
   - Entry point: Gender selection
   - States: SELECTING_FEATURE, TYPING
   - Collects specific features for a person

4. **Meta States**
   - STOPPING: Handles conversation termination
   - END: Represents the end of a conversation level

## State Mapping

The diagram highlights the important `map_to_parent` relationships that enable seamless transitions between conversation levels:

- Third level → Second level: END → SELECTING_LEVEL
- Second level → Top level: END → SELECTING_ACTION
- Any level → STOPPING: Ends the entire conversation

## Viewing the Diagram

The conversation flow diagram is available as an SVG file: [conversation_flow_diagram.svg](conversation_flow_diagram.svg)

You can view this file in any modern web browser or SVG viewer.

## Related Documentation

For a detailed explanation of the conversation structure and implementation, please refer to the [Conversation Flow Documentation](CONVERSATION_FLOW.md).
