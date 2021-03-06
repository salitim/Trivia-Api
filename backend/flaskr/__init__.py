import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin
from sqlalchemy.sql.expression import func
import random
import json

from models import setup_db, Question, Category

QUESTIONS_PER_SHELF = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_SHELF
    end = start + QUESTIONS_PER_SHELF

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
  CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
    CORS(app, resources={r"*": {"origins": "*"}},
         supports_credentials=True)
    '''
  after_request decorator to set Access-Control-Allow
  '''
    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PUT,POST,DELETE,OPTIONS')
        return response

    '''
  Create an endpoint to handle GET requests
  for all available categories.
  '''
    @app.route('/categories', methods=['GET'])
    def get_categories():
        try:
            categories = Category.query.all()
            formated_categories = {
                category.id: category.type for category in categories}
            return jsonify({
                'success': True,
                'categories': formated_categories
            })
        except:
            abort(422)
    '''
  GET requests for questions,
  including pagination (every 10 questions).
  This endpoint should return a list of questions,
  number of total questions, current category, categories.

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions.
  '''
    @app.route('/questions', methods=['GET'])
    def get_questions():
        try:
            selection = Question.query.all()
            current_questions = paginate_questions(request, selection)

            if (len(current_questions) == 0):
                abort(404)

            formated_categories = {
                category.id: category.type for category in Category.query.all()}
            return jsonify({
                'success': True,
                'questions': current_questions,
                'categories': formated_categories,
                'total_questions': len(selection),
                'current_category': []
            })
        except:
            abort(422)
    '''
  An endpoint to DELETE question using a question ID.

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page.
  '''
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(404)
            question.delete()

            selection = Question.query.all()
            current_questions = paginate_questions(request, selection)
            formated_categories = {
                category.id: category.type for category in Category.query.all()}

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': current_questions,
                'categories': formated_categories,
                'total_questions': len(selection),
                'current_category': []
            })
        except:
            abort(404)
    '''
  POST a new question,
  which  require the question and answer text,
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab,
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.
  '''
    @app.route('/questions', methods=['POST'])
    @cross_origin(supports_credentials=True)
    def create_question():
        try:
            body = request.get_json()

            new_question = body.get('question', None)
            new_answer = body.get('answer', None)
            difficulty = body.get('difficulty', None)
            category = body.get('category', None)

            question = Question(question=new_question, answer=new_answer,
                                difficulty=difficulty, category=category)
            question.insert()

            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)
            return jsonify({
                'success': True,
                'questions': current_questions,
                'created': question.id,
                'total_questions': len(Question.query.all())
            })
        except:
            abort(405)

    '''
  POST endpoint to get questions based on a search term.
  return any questions for whom the search term
  is a substring of the question.

  TEST: Search by any phrase. The questions list will update to include
  only question that include that string within their question.
  Try using the word "title" to start.
  '''

    @app.route('/questions/search', methods=['POST'])
    @cross_origin(supports_credentials=True)
    def search_question():
        try:
            body = request.get_json()
            search = body.get('searchTerm', None)

            if search:
                selection = Question.query.order_by(Question.id).filter(
                    Question.question.ilike('%{}%'.format(search)))
                current_questions = paginate_questions(request, selection)

                return jsonify({
                    'success': True,
                    'questions': current_questions,
                    'total_questions': len(Question.query.all()),
                    'current_category': []
                })
        except:
            abort(422)

    '''
  GET endpoint to get questions based on category.

  TEST: In the "List" tab / main screen, clicking on one of the
  categories in the left column will cause only questions of that
  category to be shown.
  '''
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):
        try:
            selection = Question.query.filter(
                Question.category == category_id).all()
            current_questions = paginate_questions(request, selection)
            current_category = Category.query.filter(
                Category.id == category_id).one_or_none()
            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(selection),
                'current_category': current_category.format()
            })
        except:
            abort(404)

    '''
  POST endpoint to get questions to play the quiz.
  This endpoint take category and previous question parameters
  and return a random questions within the given category,
  if provided, and that is not one of the previous questions.

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not.
  '''
    @app.route("/quizzes", methods=['POST'])
    def play_quizzes():
        current_question = Question.query.order_by(
            func.random()).first()
        if request.data:
            search_data = json.loads(request.data.decode('utf-8'))
            if (('quiz_category' in search_data
                 and 'id' in search_data['quiz_category'])
                    and 'previous_questions' in search_data):
                questions_query = Question.query.filter_by(
                    category=search_data['quiz_category']['id']
                ).filter(
                    Question.id.notin_(search_data["previous_questions"])
                ).all()
                length_of_available_question = len(questions_query)
                if length_of_available_question > 0:
                    result = {
                        "success": True,
                        "question": Question.format(
                            questions_query[random.randrange(
                                0,
                                length_of_available_question
                            )]
                        )
                    }
                else:
                    result = {
                        "success": True,
                        "question": current_question.format()
                    }
                return jsonify(result)
            abort(404)
        abort(422)
    '''
  Erros handlers for all expected errors
  including 404 and 422.
  '''
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Not found"
        }), 400

    @app.errorhandler(500)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Not authorized"
        }), 500

    return app
