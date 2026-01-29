#!/bin/bash
set -e

echo "Applying column descriptions from metadata..."

METADATA_PATH="/docker-entrypoint-initdb.d/data/livesqlbench-base-full-v1"

if [ ! -d "$METADATA_PATH" ]; then
    echo "⚠️  Warning: Metadata path $METADATA_PATH not found. Skipping column descriptions."
    exit 0
fi

# Generate SQL dynamically and pipe to psql
{
    for db_dir in "$METADATA_PATH"/*; do
        if [ -d "$db_dir" ] && [[ ! $(basename "$db_dir") =~ ^\. ]]; then
            database_name=$(basename "$db_dir")
            json_file="$db_dir/${database_name}_column_meaning_base.json"

            if [ -f "$json_file" ]; then
                echo "-- Processing metadata for $database_name" >&2
                echo "\\c $database_name"

                # Use jq to extract table, column, and description as tab-separated values
                jq -r 'to_entries[] |
                    select(.key | split("|") | length >= 3) |
                    .key as $key |
                    .value as $val |
                    ($key | split("|")) as $parts |
                    ($parts[1] | ascii_downcase) as $table |
                    ($parts[2] | ascii_downcase) as $column |
                    (
                        if ($val | type) == "object" then
                            ($val.column_meaning // "") +
                            (if $val.fields_meaning then
                                "\n\nFields Structure:\n" + ($val.fields_meaning | tojson)
                             else
                                ""
                             end)
                        else
                            ($val | tostring)
                        end
                    ) as $description |
                    [$table, $column, $description] | @tsv' "$json_file" | while IFS=$'\t' read -r table column description; do
                    # Generate SQL COMMENT statement for each column
                    cat <<EOF
DO \$do\$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = '$table'
          AND column_name = '$column'
    ) THEN
        COMMENT ON COLUMN public."$table"."$column" IS \$\$$description\$\$;
    END IF;
END \$do\$;
EOF
                done
            fi
        fi
    done
} | psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres"

echo "✅ Column descriptions applied successfully."
