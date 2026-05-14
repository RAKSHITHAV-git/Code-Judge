-- CodeJudge Database Schema
-- Run: mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS codejudge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE codejudge;

-- Users
CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(50) UNIQUE NOT NULL,
    email       VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url  VARCHAR(255) DEFAULT NULL,
    bio         TEXT DEFAULT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
);

-- Problems
CREATE TABLE IF NOT EXISTS problems (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(200) NOT NULL,
    slug            VARCHAR(200) UNIQUE NOT NULL,
    description     LONGTEXT NOT NULL,
    difficulty      ENUM('Easy', 'Medium', 'Hard') NOT NULL DEFAULT 'Easy',
    tags            JSON DEFAULT NULL,
    examples        JSON DEFAULT NULL,
    constraints     JSON DEFAULT NULL,
    time_limit_ms   INT DEFAULT 2000,
    memory_limit_mb INT DEFAULT 256,
    points          INT DEFAULT 100,
    acceptance_rate DECIMAL(5,1) DEFAULT 0.0,
    is_active       TINYINT(1) DEFAULT 1,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_difficulty (difficulty),
    INDEX idx_active (is_active)
);

-- Test Cases
CREATE TABLE IF NOT EXISTS test_cases (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    problem_id      INT NOT NULL,
    input           LONGTEXT NOT NULL,
    expected_output LONGTEXT NOT NULL,
    is_hidden       TINYINT(1) DEFAULT 0,
    FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE,
    INDEX idx_problem (problem_id)
);

-- Submissions
CREATE TABLE IF NOT EXISTS submissions (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NOT NULL,
    problem_id      INT NOT NULL,
    code            LONGTEXT NOT NULL,
    language        VARCHAR(20) NOT NULL DEFAULT 'python',
    verdict         ENUM('AC','WA','TLE','MLE','RE','CE') NOT NULL DEFAULT 'WA',
    passed_cases    INT DEFAULT 0,
    total_cases     INT DEFAULT 0,
    exec_time_ms    INT DEFAULT 0,
    memory_kb       INT DEFAULT 0,
    submitted_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_problem (problem_id),
    INDEX idx_verdict (verdict)
);

-- ── Seed Problems ──────────────────────────────────────────────────────────────

INSERT INTO problems (title, slug, description, difficulty, tags, examples, constraints, points) VALUES
(
  'Two Sum',
  'two-sum',
  'Given an array of integers `nums` and an integer `target`, return *indices of the two numbers such that they add up to target*.\n\nYou may assume that each input would have **exactly one solution**, and you may not use the same element twice.\n\nYou can return the answer in any order.',
  'Easy',
  '["Array", "Hash Table"]',
  '[{"input": "nums = [2,7,11,15], target = 9", "output": "[0, 1]", "explanation": "Because nums[0] + nums[1] == 9, we return [0, 1]."}, {"input": "nums = [3,2,4], target = 6", "output": "[1, 2]"}]',
  '["2 <= nums.length <= 10^4", "-10^9 <= nums[i] <= 10^9", "-10^9 <= target <= 10^9", "Only one valid answer exists."]',
  100
),
(
  'Reverse a String',
  'reverse-string',
  'Write a function that reverses a string.\n\nThe input is given as a single line string. Output the reversed string.\n\n**Example:**\n- Input: `hello`\n- Output: `olleh`',
  'Easy',
  '["String", "Two Pointers"]',
  '[{"input": "hello", "output": "olleh"}, {"input": "abcde", "output": "edcba"}]',
  '["1 <= s.length <= 10^5", "s consists of printable ASCII characters"]',
  80
),
(
  'FizzBuzz',
  'fizzbuzz',
  'Given an integer `n`, print numbers from 1 to n with these rules:\n- For multiples of 3, print `Fizz`\n- For multiples of 5, print `Buzz`\n- For multiples of both 3 and 5, print `FizzBuzz`\n- Otherwise print the number\n\nEach value on a separate line.',
  'Easy',
  '["Math", "String", "Simulation"]',
  '[{"input": "15", "output": "1\\n2\\nFizz\\n4\\nBuzz\\nFizz\\n7\\n8\\nFizz\\nBuzz\\n11\\nFizz\\n13\\n14\\nFizzBuzz"}]',
  '["1 <= n <= 10^4"]',
  80
),
(
  'Palindrome Check',
  'palindrome-check',
  'Given a string, determine if it is a palindrome.\n\nA palindrome reads the same forwards and backwards. Consider only alphanumeric characters and ignore cases.\n\nOutput `true` if palindrome, `false` otherwise.',
  'Easy',
  '["String", "Two Pointers"]',
  '[{"input": "A man a plan a canal Panama", "output": "true"}, {"input": "race a car", "output": "false"}]',
  '["1 <= s.length <= 2 * 10^5"]',
  90
),
(
  'Valid Parentheses',
  'valid-parentheses',
  'Given a string `s` containing just the characters `(`, `)`, `{`, `}`, `[` and `]`, determine if the input string is valid.\n\nAn input string is valid if:\n1. Open brackets must be closed by the same type of brackets.\n2. Open brackets must be closed in the correct order.\n3. Every close bracket has a corresponding open bracket of the same type.\n\nOutput `true` or `false`.',
  'Easy',
  '["String", "Stack"]',
  '[{"input": "()", "output": "true"}, {"input": "()[]{}", "output": "true"}, {"input": "(]", "output": "false"}]',
  '["1 <= s.length <= 10^4", "s consists of parentheses only"]',
  100
),
(
  'Longest Common Prefix',
  'longest-common-prefix',
  'Write a function to find the longest common prefix string amongst an array of strings.\n\nIf there is no common prefix, return an empty string `""`.\n\nInput: first line is n (number of strings), then n strings one per line.\nOutput: the longest common prefix.',
  'Easy',
  '["String", "Trie"]',
  '[{"input": "3\\nflower\\nflow\\nflight", "output": "fl"}, {"input": "3\\ndog\\nracecar\\ncar", "output": ""}]',
  '["1 <= strs.length <= 200", "0 <= strs[i].length <= 200"]',
  110
),
(
  'Maximum Subarray',
  'maximum-subarray',
  'Given an integer array `nums`, find the subarray with the largest sum, and return its sum.\n\nInput: first line n, second line n space-separated integers.',
  'Medium',
  '["Array", "Dynamic Programming", "Divide and Conquer"]',
  '[{"input": "9\\n-2 1 -3 4 -1 2 1 -5 4", "output": "6"}, {"input": "1\\n1", "output": "1"}]',
  '["1 <= nums.length <= 10^5", "-10^4 <= nums[i] <= 10^4"]',
  150
),
(
  'Binary Search',
  'binary-search',
  'Given an array of integers `nums` sorted in ascending order, and an integer `target`, write a function to search `target` in `nums`. If `target` exists, return its index. Otherwise, return `-1`.\n\nYou must write an algorithm with O(log n) runtime complexity.\n\nInput: first line n, second line n sorted integers, third line target.',
  'Easy',
  '["Array", "Binary Search"]',
  '[{"input": "6\\n-1 0 3 5 9 12\\n9", "output": "4"}, {"input": "6\\n-1 0 3 5 9 12\\n2", "output": "-1"}]',
  '["1 <= nums.length <= 10^4", "-10^4 < nums[i], target < 10^4"]',
  100
),
(
  'Merge Two Sorted Lists',
  'merge-sorted-lists',
  'You are given two sorted arrays. Merge them into one sorted array and print the result as space-separated integers.\n\nInput: first line has array 1 (space-separated), second line has array 2.',
  'Easy',
  '["Array", "Sorting", "Merge Sort"]',
  '[{"input": "1 2 4\\n1 3 4", "output": "1 1 2 3 4 4"}, {"input": "\\n0", "output": "0"}]',
  '["0 <= list1.length, list2.length <= 50", "-100 <= values <= 100"]',
  100
),
(
  'Climbing Stairs',
  'climbing-stairs',
  'You are climbing a staircase. It takes `n` steps to reach the top.\n\nEach time you can either climb 1 or 2 steps. In how many distinct ways can you climb to the top?\n\nInput: single integer n.',
  'Easy',
  '["Math", "Dynamic Programming", "Memoization"]',
  '[{"input": "2", "output": "2"}, {"input": "3", "output": "3"}]',
  '["1 <= n <= 45"]',
  120
),
(
  'Number of Islands',
  'number-of-islands',
  'Given an m×n 2D binary grid which represents a map of `1`s (land) and `0`s (water), return the number of islands.\n\nAn island is surrounded by water and is formed by connecting adjacent lands horizontally or vertically.\n\nInput: first line "m n", then m lines of n space-separated values (0 or 1).',
  'Medium',
  '["Array", "DFS", "BFS", "Union Find"]',
  '[{"input": "4 5\\n1 1 1 1 0\\n1 1 0 1 0\\n1 1 0 0 0\\n0 0 0 0 0", "output": "1"}, {"input": "4 5\\n1 1 0 0 0\\n1 1 0 0 0\\n0 0 1 0 0\\n0 0 0 1 1", "output": "3"}]',
  '["m == grid.length", "n == grid[i].length", "1 <= m, n <= 300"]',
  200
),
(
  'Longest Palindromic Substring',
  'longest-palindromic-substring',
  'Given a string `s`, return the longest palindromic substring in `s`.\n\nIf there are multiple valid answers, return any one.',
  'Medium',
  '["String", "Dynamic Programming", "Two Pointers"]',
  '[{"input": "babad", "output": "bab"}, {"input": "cbbd", "output": "bb"}]',
  '["1 <= s.length <= 1000", "s consist of only digits and English letters"]',
  180
);

-- ── Seed Test Cases ────────────────────────────────────────────────────────────

-- Two Sum (id=1)
INSERT INTO test_cases (problem_id, input, expected_output, is_hidden) VALUES
(1, '4\n2 7 11 15\n9', '[0, 1]', 0),
(1, '3\n3 2 4\n6', '[1, 2]', 0),
(1, '2\n3 3\n6', '[0, 1]', 1),
(1, '5\n1 5 3 8 2\n10', '[1, 3]', 1);

-- Reverse String (id=2)
INSERT INTO test_cases (problem_id, input, expected_output, is_hidden) VALUES
(2, 'hello', 'olleh', 0),
(2, 'abcde', 'edcba', 0),
(2, 'a', 'a', 1),
(2, 'racecar', 'racecar', 1),
(2, 'OpenAI', 'IAnepO', 1);

-- FizzBuzz (id=3)
INSERT INTO test_cases (problem_id, input, expected_output, is_hidden) VALUES
(3, '15', '1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz', 0),
(3, '5', '1\n2\nFizz\n4\nBuzz', 0),
(3, '1', '1', 1),
(3, '20', '1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz\n16\n17\nFizz\n19\nBuzz', 1);

-- Palindrome (id=4)
INSERT INTO test_cases (problem_id, input, expected_output, is_hidden) VALUES
(4, 'A man a plan a canal Panama', 'true', 0),
(4, 'race a car', 'false', 0),
(4, ' ', 'true', 1),
(4, 'Was it a car or a cat I saw', 'true', 1);

-- Valid Parentheses (id=5)
INSERT INTO test_cases (problem_id, input, expected_output, is_hidden) VALUES
(5, '()', 'true', 0),
(5, '()[]{}", "true', 'true', 0),
(5, '(]', 'false', 0),
(5, '([)]', 'false', 1),
(5, '{[]}', 'true', 1);

-- Longest Common Prefix (id=6)
INSERT INTO test_cases (problem_id, input, expected_output, is_hidden) VALUES
(6, '3\nflower\nflow\nflight', 'fl', 0),
(6, '3\ndog\nracecar\ncar', '', 0),
(6, '1\nalone', 'alone', 1),
(6, '2\ninterstellar\ninteractive', 'inter', 1);

-- Maximum Subarray (id=7)
INSERT INTO test_cases (problem_id, input, expected_output, is_hidden) VALUES
(7, '9\n-2 1 -3 4 -1 2 1 -5 4', '6', 0),
(7, '1\n1', '1', 0),
(7, '5\n5 4 -1 7 8', '23', 1),
(7, '3\n-2 -1 -3', '-1', 1);

-- Binary Search (id=8)
INSERT INTO test_cases (problem_id, input, expected_output, is_hidden) VALUES
(8, '6\n-1 0 3 5 9 12\n9', '4', 0),
(8, '6\n-1 0 3 5 9 12\n2', '-1', 0),
(8, '1\n5\n5', '0', 1),
(8, '4\n1 3 5 7\n3', '1', 1);

-- Merge Sorted Lists (id=9)
INSERT INTO test_cases (problem_id, input, expected_output, is_hidden) VALUES
(9, '1 2 4\n1 3 4', '1 1 2 3 4 4', 0),
(9, '\n0', '0', 0),
(9, '1 2 3\n4 5 6', '1 2 3 4 5 6', 1);

-- Climbing Stairs (id=10)
INSERT INTO test_cases (problem_id, input, expected_output, is_hidden) VALUES
(10, '2', '2', 0),
(10, '3', '3', 0),
(10, '1', '1', 1),
(10, '10', '89', 1),
(10, '45', '1836311903', 1);

-- Number of Islands (id=11)
INSERT INTO test_cases (problem_id, input, expected_output, is_hidden) VALUES
(11, '4 5\n1 1 1 1 0\n1 1 0 1 0\n1 1 0 0 0\n0 0 0 0 0', '1', 0),
(11, '4 5\n1 1 0 0 0\n1 1 0 0 0\n0 0 1 0 0\n0 0 0 1 1', '3', 0),
(11, '1 1\n1', '1', 1);

-- Longest Palindromic Substring (id=12)
INSERT INTO test_cases (problem_id, input, expected_output, is_hidden) VALUES
(12, 'babad', 'bab', 0),
(12, 'cbbd', 'bb', 0),
(12, 'a', 'a', 1),
(12, 'racecar', 'racecar', 1);
