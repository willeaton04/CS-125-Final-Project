#!/bin/bash

# GraphQL Endpoint Test Script
# Tests all queries and mutations in the schema

# Configuration
GRAPHQL_URL="http://localhost:8001/graphql"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Function to print test name
print_test() {
    echo -e "${YELLOW}Testing: $1${NC}"
}

# Function to execute GraphQL query
execute_query() {
    local query=$1
    local description=$2

    print_test "$description"

    response=$(curl -s -X POST "$GRAPHQL_URL" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"$query\"}")

    if echo "$response" | grep -q "\"errors\""; then
        echo -e "${RED}❌ FAILED${NC}"
        echo "$response" | jq '.'
    else
        echo -e "${GREEN}✅ PASSED${NC}"
        echo "$response" | jq '.'
    fi
    echo ""
}

# ======================
# QUERY TESTS
# ======================

print_header "TESTING QUERIES"

# Test: Get all students
execute_query "query { students { student_name parent_name email phone_number small_group_name small_group_leader_name note } }" \
    "Get all students"

# Test: Get single student
execute_query "query { student(studentId: 1) { student_name parent_name email phone_number } }" \
    "Get student by ID"

# Test: Get all parents
execute_query "query { parents { parent_id parent_name email phone_number note students } }" \
    "Get all parents"

# Test: Get all leaders
execute_query "query { leaders { leader_id leader_name small_group_name datejoined email phone_number salary note shifts { start_time end_time } } }" \
    "Get all leaders"

# Test: Get single leader
execute_query "query { leader(leaderId: 1) { leader_id leader_name email phone_number salary } }" \
    "Get leader by ID"

# Test: Get all events
execute_query "query { events { StartTime EndTime description } }" \
    "Get all events"

# Test: Get single event
execute_query "query { event(eventId: 1) { StartTime EndTime studentId VenueAdress description } }" \
    "Get event by ID"

# Test: Get all camps
execute_query "query { camps { CampNumber StartTime EndTime Description VenueDescription VenueAddress } }" \
    "Get all camps"

# Test: Get single camp
execute_query "query { camp(campId: 1) { CampNumber StartTime EndTime description } }" \
    "Get camp by ID"

# Test: Get all venues
execute_query "query { venues { VenueAdress description } }" \
    "Get all venues"

# Test: Get single venue
execute_query "query { venue(venueId: 1) { VenueAdress description } }" \
    "Get venue by ID"

# Test: Get camp registration
execute_query "query { campRegistration(campId: 1) { campId AmountPaid description VenueAdress } }" \
    "Get camp registration by camp ID"

# Test: Get leader small group
execute_query "query { leaderSmallGroup(leaderId: 1) { small_group_name meeting_time student_name } }" \
    "Get leader's small group"

# Test: Get event attendance
execute_query "query { eventAttendance(eventId: 1) { event_id student_id first_name last_name email phone_number timestamp note } }" \
    "Get event attendance"

# Test: Get camp registration by student
execute_query "query { campRegistrationStudent(studentId: 1) { student_name campId registered_time amount_paid parent_name description venue_address } }" \
    "Get camp registration by student ID"

# Test: Get Redis event registration
execute_query "query { redisEventRegistration(eventId: 1) { event_id count success message registrations { student_id first_name last_name email } } }" \
    "Get Redis event registration"

# ======================
# MUTATION TESTS
# ======================

print_header "TESTING MUTATIONS"

# Test: Load Redis event registration
execute_query "mutation { loadRedisEventRegistration(eventId: 1) }" \
    "Load Redis event registration"

# Test: Update student
execute_query "mutation { updateStudent(studentId: 1, input: { email: \\\"updated@example.com\\\", phoneNumber: \\\"555-0001\\\" }) }" \
    "Update student"

# Test: Update parent
execute_query "mutation { updateParent(parentId: 1, input: { email: \\\"parent_updated@example.com\\\", phoneNumber: \\\"555-0002\\\" }) }" \
    "Update parent"

# Test: Update leader
execute_query "mutation { updateLeader(leaderId: 1, input: { email: \\\"leader_updated@example.com\\\", salary: 50000.0 }) }" \
    "Update leader"

# Test: Update event
execute_query "mutation { updateEvent(eventId: 1, input: { description: \\\"Updated event description\\\" }) }" \
    "Update event"

# Test: Create MongoDB event
execute_query "mutation { createMongoEvent(input: { venueId: 1, startTime: \\\"2024-12-20 10:00:00\\\", endTime: \\\"2024-12-20 12:00:00\\\", description: \\\"Test Event\\\", customFields: { theme: \\\"Christmas\\\" } }) }" \
    "Create MongoDB event"

# Test: Create MongoDB camp
execute_query "mutation { createMongoCamp(input: { venueId: 1, startTime: \\\"2024-12-25 09:00:00\\\", endTime: \\\"2024-12-27 17:00:00\\\", description: \\\"Winter Camp\\\", customFields: { capacity: 50 } }) }" \
    "Create MongoDB camp"

# Test: Update camp
execute_query "mutation { updateCamp(campId: 1, input: { description: \\\"Updated camp description\\\" }) }" \
    "Update camp"

# Test: Update venue
execute_query "mutation { updateVenue(venueId: 1, input: { description: \\\"Updated venue description\\\" }) }" \
    "Update venue"

# Test: Update Redis event registration
execute_query "mutation { updateRedisEventRegistration(eventId: 1) }" \
    "Update Redis event registration"

# ======================
# DESTRUCTIVE TESTS (commented out by default)
# ======================

print_header "DESTRUCTIVE TESTS (Commented Out)"
echo "Uncomment these tests if you want to test delete operations"
echo ""

# Test: Delete Redis event registration
# execute_query "mutation { deleteRedisEventRegistration(eventId: 1) }" \
#     "Delete Redis event registration"

# Test: Delete student
# execute_query "mutation { deleteStudent(studentId: 999) }" \
#     "Delete student"

# Test: Delete parent
# execute_query "mutation { deleteParent(parentId: 999) }" \
#     "Delete parent"

# Test: Delete leader
# execute_query "mutation { deleteLeader(leaderId: 999) }" \
#     "Delete leader"

# Test: Delete event
# execute_query "mutation { deleteEvent(eventId: 999) }" \
#     "Delete event"

# Test: Delete camp
# execute_query "mutation { deleteCamp(campId: 999) }" \
#     "Delete camp"

# Test: Delete venue
# execute_query "mutation { deleteVenue(venueId: 999) }" \
#     "Delete venue"

# ======================
# SUMMARY
# ======================

print_header "TEST SUITE COMPLETED"
echo -e "${GREEN}All tests have been executed.${NC}"
echo -e "${YELLOW}Note: Some tests may fail if IDs don't exist in your database.${NC}"
echo -e "${YELLOW}Adjust the IDs in the script according to your database state.${NC}"
echo ""