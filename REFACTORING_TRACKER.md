# Issues.py Refactoring Tracker

## 📊 **Current Status: PLANNING → EXECUTION**

**Original File:** `youtrack_mcp/tools/issues.py` (1797 lines)
**Target:** Modular structure with 6-8 focused files (~200-400 lines each)

## 🎯 **Refactoring Structure**

### **New Directory Structure:**
```
youtrack_mcp/tools/issues/
├── __init__.py              # Main IssueTools class (orchestrator)
├── basic_operations.py      # Core CRUD operations  
├── custom_fields.py         # Custom field management
├── dedicated_updates.py     # ✅ COMPLETED - Specialized update functions  
├── linking.py              # Issue relationships
├── diagnostics.py          # Workflow analysis & help
└── attachments.py          # File & raw data operations
```

## 📋 **Function Inventory & Refactoring Status**

### **✅ COMPLETED: 24/28 functions**

### **🔄 IN PROGRESS: 0/28 functions**

### **⏳ PENDING: 4/28 functions**

#### **dedicated_updates.py (5 functions) - ✅ COMPLETED + TESTED**
- [x] `update_issue_state` - State transitions (newly enhanced) ✅ 
- [x] `update_issue_priority` - Priority changes (newly enhanced) ✅
- [x] `update_issue_assignee` - Assignment changes (newly created) ✅
- [x] `update_issue_type` - Type changes (newly created) ✅
- [x] `update_issue_estimation` - Time estimates (newly created) ✅

**✅ Includes comprehensive tests covering:**
- Enhanced workflow error handling with specific guidance
- HTTP 405 error detection and messaging
- Submitted → Open workflow restriction scenarios  
- In Progress assignee requirement scenarios
- Field-specific error guidance and troubleshooting
- Fallback mechanisms (Direct API → Commands API)
- Parameter validation and exception handling
- Tool definitions validation

#### **diagnostics.py (2 functions) - ✅ COMPLETED + TESTED**
- [x] `diagnose_workflow_restrictions` - Workflow analysis (newly enhanced) ✅
- [x] `get_help` - Interactive help (newly created) ✅

**✅ Includes comprehensive tests covering:**
- State machine vs direct field workflow detection
- Available transition analysis with event mapping
- Permission restriction identification
- Technical notes and troubleshooting guidance
- Interactive help system with topic-based content
- Workflow-specific guidance and best practices
- Error handling and edge cases
- Tool definitions validation

#### **custom_fields.py (5 functions) - ✅ COMPLETED + TESTED**
- [x] `update_custom_fields` - General custom field updates ✅
- [x] `batch_update_custom_fields` - Bulk custom field operations ✅
- [x] `get_custom_fields` - Get issue custom fields ✅
- [x] `validate_custom_field` - Validate field values ✅
- [x] `get_available_custom_field_values` - Get allowed field values ✅

**✅ Includes comprehensive tests covering:**
- Field value updates with validation enabled/disabled
- Batch operations with mixed success/error results
- Field validation against project schemas
- Available value retrieval with error handling
- Missing parameter validation
- API error handling with detailed feedback
- Model dump response handling
- Tool definitions validation

#### **basic_operations.py (5 functions) - ✅ COMPLETED + TESTED**
- [x] `get_issue` - Get issue information ✅
- [x] `search_issues` - Search with YouTrack query language ✅
- [x] `create_issue` - Create new issues ✅
- [x] `update_issue` - Update issue summary/description ✅
- [x] `add_comment` - Add comments to issues ✅

**✅ Includes comprehensive tests covering:**
- Issue retrieval with comprehensive field data
- Issue search with YouTrack query language support
- Issue creation with project validation (name/ID conversion)
- Issue updates with flexible parameter handling
- Comment addition with proper error handling
- Missing parameter validation for all functions
- API error handling with detailed feedback
- Project lookup and detailed issue retrieval
- Tool definitions validation

#### **linking.py (7 functions) - ✅ COMPLETED + TESTED**
- [x] `link_issues` - Generic issue linking ✅
- [x] `get_issue_links` - Get all issue relationships ✅
- [x] `get_available_link_types` - Get available link types ✅
- [x] `add_dependency` - Create dependencies ✅
- [x] `remove_dependency` - Remove dependencies ✅
- [x] `add_relates_link` - Add "relates" relationships ✅
- [x] `add_duplicate_link` - Mark as duplicate ✅

**✅ Includes comprehensive tests covering:**
- Generic issue linking with various link types
- Issue dependency management (depends on/blocks relationships)
- Specialized relationship creation (relates, duplicates)
- Link retrieval and available link types discovery
- Dependency removal with command-based operations
- Parametrized testing with multiple link types
- Non-dict response handling for command operations
- Tool definitions validation for all 7 functions

#### **attachments.py (2 functions)**
- [ ] `get_issue_raw` - Raw issue data
- [ ] `get_attachment_content` - File attachments as base64

#### **Utility Methods (2 functions)**
- [ ] `get_tool_definitions` - Tool configuration
- [ ] `close` - Cleanup method

## 🧪 **Testing Strategy**

### **Test Files to Create:**
```
tests/unit/tools/issues/
├── test_basic_operations.py
├── test_custom_fields.py  
├── test_dedicated_updates.py    # ⭐ PRIORITY
├── test_linking.py
├── test_diagnostics.py          # ⭐ PRIORITY  
├── test_attachments.py
└── test_integration.py
```

### **Test Priorities:**
1. **🔥 HIGH:** `dedicated_updates.py` - New functions with enhanced error handling
2. **🔥 HIGH:** `diagnostics.py` - Workflow analysis and help system
3. **⚡ MEDIUM:** `custom_fields.py` - Core functionality
4. **⚡ MEDIUM:** `basic_operations.py` - CRUD operations
5. **📝 LOW:** `linking.py`, `attachments.py` - Specialized features

## 🎯 **Refactoring Goals**

### **✅ Maintainability**
- [ ] Break 1797-line monolith into focused modules
- [ ] Clear separation of concerns  
- [ ] Improved code discoverability

### **✅ Testing**
- [ ] Comprehensive unit test coverage
- [ ] Integration tests for critical workflows
- [ ] Mock-based testing for API interactions

### **✅ Documentation**
- [ ] Per-module documentation
- [ ] Updated function signatures
- [ ] Clear import/export patterns

## 📈 **Progress Tracking**

**Started:** [Date]
**Target Completion:** [Date + 2 days]

### **Daily Progress:**
- **Day 1:** Structure setup + basic_operations + dedicated_updates
- **Day 2:** custom_fields + diagnostics + testing
- **Day 3:** linking + attachments + integration tests

## 🚀 **Next Steps**

1. **Create directory structure**
2. **Refactor dedicated_updates.py (highest priority)**
3. **Create comprehensive tests** 
4. **Update main issues.py to import from modules**
5. **Validate all functions work correctly**

---

**🎉 SUCCESS CRITERIA:**
- All 28 functions successfully refactored
- 100% test coverage for critical functions
- No breaking changes to existing API
- Improved code maintainability and readability 