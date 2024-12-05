'''
contains all sql queries that will be executed by mysql_vector
'''
from __future__ import annotations

from .distance import Distance


_CREATE_COLLECTION_PROC = \
    '''
CREATE PROCEDURE create_collection (IN collection_name VARCHAR(255), IN dimension INT)
BEGIN
    SET @query = CONCAT(
        'CREATE TABLE IF NOT EXISTS ', collection_name, ' (',
        'vector_id INT AUTO_INCREMENT PRIMARY KEY, ',
        'vector JSON, ',
        'normalized_vector JSON, ',
        'magnitude DOUBLE, ',
        'binary_code BINARY(', dimension, '), ',
        'payload JSON, ',
        'created TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        ')'
    );

    PREPARE stmt FROM @query;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END
'''

_DIST_COSINE_FUNC = \
    '''
CREATE FUNCTION DIST_COSINE(v1 JSON, v2 JSON)
RETURNS FLOAT DETERMINISTIC
BEGIN
    DECLARE sim FLOAT DEFAULT 0;
    DECLARE i INT DEFAULT 0;
    DECLARE len INT DEFAULT JSON_LENGTH(v1);
    WHILE i < len DO
        SET sim = sim + (JSON_EXTRACT(v1, CONCAT('$[', i, ']')) * JSON_EXTRACT(v2, CONCAT('$[', i, ']')));
        SET i = i + 1;
    END WHILE;
    RETURN SIM;
END
'''

_DIST_EUCLID_FUNC = \
    '''
CREATE FUNCTION DIST_EUCLID(v1 JSON, v2 JSON)
RETURNS FLOAT DETERMINISTIC
BEGIN
    DECLARE dot_prod FLOAT DEFAULT 0;
    DECLARE i INT DEFAULT 0;
    DECLARE len INT DEFAULT JSON_LENGTH(v1);
    WHILE i < len DO
        SET dot_prod = dot_prod + (JSON_EXTRACT(v1, CONCAT('$[', i, ']')) * JSON_EXTRACT(v2, CONCAT('$[', i, ']')));
        SET i = i + 1;
    END WHILE;
    SET dot_prod = SQRT(2 * (1 - dot_prod));
    RETURN dot_prod;
END
'''

_DIST_DOT_FUNC = \
    '''
CREATE FUNCTION DIST_DOT(v1 JSON, v2 JSON)
RETURNS FLOAT DETERMINISTIC
BEGIN
    DECLARE dot_prod FLOAT DEFAULT 0;
    DECLARE i INT DEFAULT 0;
    DECLARE len INT DEFAULT JSON_LENGTH(v1);
    WHILE i < len DO
        SET dot_prod = dot_prod + (JSON_EXTRACT(v1, CONCAT('$[', i, ']')) * JSON_EXTRACT(v2, CONCAT('$[', i, ']')));
        SET i = i + 1;
    END WHILE;
    RETURN dot_prod;
END
'''

_DIST_MANHATTAN_FUNC = \
    '''
CREATE FUNCTION DIST_MANHATTAN(v1 JSON, v2 JSON)
RETURNS FLOAT DETERMINISTIC
BEGIN
    DECLARE dist FLOAT DEFAULT 0;
    DECLARE i INT DEFAULT 0;
    DECLARE len INT DEFAULT JSON_LENGTH(v1);
    WHILE i < len DO
        SET dist = dist + (JSON_EXTRACT(v1, CONCAT('$[', i, ']')) - JSON_EXTRACT(v2, CONCAT('$[', i, ']')));
        SET i = i + 1;
    END WHILE;
    RETURN dist;
END
'''

_SEARCH_QUERY_GET_CANDIDATES = \
    '''
SELECT vector_id, BIT_COUNT(binary_code ^ UNHEX(%s)) AS hamming_distance
FROM <collection_name>
ORDER BY hamming_distance
LIMIT %s
'''


_SEARCH_QUERY_GET_VECTORS = \
    '''
SELECT vector_id, vector, payload, <dist_func>(normalized_vector, %s) AS sim
FROM <collection_name>
WHERE vector_id IN (<placeholders>)
ORDER BY sim DESC LIMIT %s
'''


class Queries:
    DATABASE_NAME = '_vector_db_collection'

    @staticmethod
    def get_version() -> str:
        return 'select version();'

    @staticmethod
    def create_collection_proc() -> str:
        return _CREATE_COLLECTION_PROC

    @staticmethod
    def drop_collection_proc() -> str:
        return 'DROP PROCEDURE IF EXISTS create_collection'

    @staticmethod
    def define_dist_cosine_func() -> str:
        return _DIST_COSINE_FUNC

    @staticmethod
    def drop_dist_cosine_func() -> str:
        return 'DROP FUNCTION IF EXISTS DIST_COSINE'

    @staticmethod
    def define_dist_euclid_func() -> str:
        return _DIST_EUCLID_FUNC

    @staticmethod
    def drop_dist_euclid_func() -> str:
        return 'DROP FUNCTION IF EXISTS DIST_EUCLID'

    @staticmethod
    def define_dist_dot_func() -> str:
        return _DIST_DOT_FUNC

    @staticmethod
    def drop_dist_dot_func() -> str:
        return 'DROP FUNCTION IF EXISTS DIST_DOT'

    @staticmethod
    def define_dist_manhattan_func() -> str:
        return _DIST_MANHATTAN_FUNC

    @staticmethod
    def drop_dist_manhattan_func() -> str:
        return 'DROP FUNCTION IF EXISTS DIST_MANHATTAN'

    @staticmethod
    def create_db() -> str:
        return f'CREATE DATABASE IF NOT EXISTS {Queries.DATABASE_NAME};'

    @staticmethod
    def switch_to_db() -> str:
        return f'USE {Queries.DATABASE_NAME}'

    @staticmethod
    def create_collection_proc_name() -> str:
        return 'create_collection'

    @staticmethod
    def insert_to_collection(name: str) -> str:
        return \
            f'INSERT INTO {name} '\
            '(vector, normalized_vector, magnitude, binary_code, payload) VALUES (%s, %s, %s, UNHEX(%s), %s)'

    @staticmethod
    def get_search_candidates(collection_name: str) -> str:
        return _SEARCH_QUERY_GET_CANDIDATES.replace('<collection_name>', collection_name)

    @staticmethod
    def get_search_vectors(collection_name: str, placeholders: str, distance: Distance) -> str:
        dist_func_names = {
            Distance.COSINE: 'DIST_COSINE',
            Distance.EUCLID: 'DIST_EUCLID',
            Distance.DOT: 'DIST_DOT',
            Distance.MANHATTAN: 'DIST_MANHATTAN'
        }

        if distance not in dist_func_names:
            raise NotImplementedError(
                f'Function for {distance} is not implemented',
            )

        return _SEARCH_QUERY_GET_VECTORS\
            .replace('<collection_name>', collection_name)\
            .replace('<placeholders>', placeholders)\
            .replace('<dist_func>', dist_func_names[distance])

    @staticmethod
    def delete_collection(name: str) -> str:
        return f'DROP TABLE IF EXISTS {name}'
