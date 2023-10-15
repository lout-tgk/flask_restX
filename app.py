from flask import Flask, request, render_template
from flask_restx import Api, Resource, fields
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc, desc, func
import os

basedir = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'countries.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

api = Api(app, doc='/api', title="A country API", description="A simple REST API for countries")

db = SQLAlchemy(app)


class Country(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    country_name = db.Column(db.String(40), nullable=False)
    capital_of_the_country = db.Column(db.String(10), nullable=False)
    living_standard = db.Column(db.String(80), nullable=False)
    country_area = db.Column(db.Integer(), nullable=False)
    population_of_the_country = db.Column(db.Integer(), nullable=False)
    phone_code = db.Column(db.Integer(), nullable=False)

    def __repr__(self):
        return self.country_name


country_model = api.model(
    'country',
    {
        'id': fields.Integer(),
        'country_name': fields.String(),
        'capital_of_the_country': fields.String(),
        'living_standard': fields.String(),
        'country_area': fields.Integer(),
        'population_of_the_country': fields.Integer(),
        'phone_code': fields.Integer()
    }
)


@api.route('/api/countries')
class Countries(Resource):

    @api.marshal_list_with(country_model, code=200)
    def get(self):
        """ Get all countries """

        sort_by = request.args.get('sort')
        sort_order = request.args.get('order', default='asc')

        sort_dirs = {"desc": desc, "asc": asc}
        sort_dir_func = sort_dirs.get(sort_order, sort_dirs["asc"])

        countries = Country.query

        if sort_by is not None and hasattr(Country, sort_by):
            countries = countries.order_by(sort_dir_func
                                           (getattr(Country, sort_by)))

        return countries.all()

    @api.marshal_with(country_model, code=201, envelope="country")
    def post(self):
        """ Create a new countries """

        data = request.get_json()

        country_name = data.get('country_name')
        capital_of_the_country = data.get('capital_of_the_country')
        living_standard = data.get('living_standard')
        country_area = data.get('country_area')
        population_of_the_country = data.get('population_of_the_country')
        phone_code = data.get('phone_code')

        new_country = Country(country_name=country_name, capital_of_the_country=capital_of_the_country,
                              living_standard=living_standard, country_area=country_area,
                              population_of_the_country=population_of_the_country, phone_code=phone_code)

        db.session.add(new_country)

        db.session.commit()

        return new_country


@api.route('/api/countries/max_value/<string:field>')
class CountryWithMaxValue(Resource):
    @api.marshal_with(country_model, code=200)
    def get(self, field):
        """ Get country with maximum value for the given field """
        field_attribute = getattr(Country, field)
        country = Country.query.order_by(field_attribute.desc()).first()
        return country


@api.route('/api/countries/min_value/<string:field>')
class CountryWithMinValue(Resource):
    @api.marshal_with(country_model, code=200)
    def get(self, field):
        """ Get country with minimum value for the given field """
        field_attribute = getattr(Country, field)
        country = Country.query.order_by(field_attribute.asc()).first()
        return country


@api.route('/api/countries/average_value/<string:field>')
class CountryAverageValue(Resource):
    @staticmethod
    def get(field):
        """ Get average value for the given field """
        field_attribute = getattr(Country, field)
        average_value = db.session.query(func.avg(field_attribute)).scalar()
        result = {'field': field, 'average_value': average_value}

        return result


@api.route('/api/country/<int:id>')
class CountryResource(Resource):

    @api.marshal_with(country_model, code=200, envelope="country")
    def get(self, id):
        """ Get a country by id """
        country = Country.query.get_or_404(id)

        return country, 200

    @api.marshal_with(country_model, envelope="country", code=200)
    def put(self, id):
        """ Update a country """
        country_to_update = Country.query.get_or_404(id)

        data = request.get_json()

        country_to_update.country_name = data.get('country_name')
        country_to_update.capital_of_the_country = data.get('capital_of_the_country')
        country_to_update.living_standard = data.get('living_standard')
        country_to_update.country_area = data.get('country_area')
        country_to_update.population_of_the_country = data.get('population_of_the_country')
        country_to_update.phone_code = data.get('phone_code')

        db.session.commit()

        return country_to_update, 200

    @api.marshal_with(country_model, envelope="country_deleted", code=200)
    def delete(self, id):
        """ Delete a country """
        country_to_delete = Country.query.get_or_404(id)

        db.session.delete(country_to_delete)

        db.session.commit()

        return country_to_delete, 200


@app.route('/countries', methods=['GET', 'POST'])
def index():
    # if request.method == 'POST':
    countries = Country.query.all()
    return render_template('index.html', countries=countries)


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'country': Country
    }


if __name__ == "__main__":
    app.run(debug=True)
