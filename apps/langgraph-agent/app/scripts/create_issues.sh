TYPE=$(jq -r ".issues[$i].type // \"\"" "$TASK_FILE")
EPIC=$(jq -r ".issues[$i].epic // \"\"" "$TASK_FILE")
SP=$(jq -r ".issues[$i].storyPoints // 0" "$TASK_FILE")

EXTRA_LABELS=$(jq -c ".issues[$i].labels // []" "$TASK_FILE")
# Construir labels finales: defaultLabels + type/epic/SP + extra
LABELS=$(jq -n \
  --arg sprint "$SPRINT" \
  --arg type "$TYPE" \
  --arg epic "$EPIC" \
  --arg sp "SP: $SP" \
  --argjson extra "$EXTRA_LABELS" '
    ($extra + 
     (if $sprint != "" then [$sprint] else [] end) +
     (if $type  != "" then ["Type: " + $type] else [] end) +
     (if $epic  != "" then ["Epic: " + $epic] else [] end) +
     (if $sp    != "SP: 0" then [$sp] else [] end)
    )')

PAYLOAD=$(jq -n \
  --arg title "$TITLE" \
  --arg body "$BODY" \
  --argjson labels "$LABELS" \
  --argjson assignees "$(jq -c ".issues[$i].assignees // []" "$TASK_FILE")" '
    {title: $title, body: $body, labels: $labels, assignees: $assignees}')
