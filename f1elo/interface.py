import datetime
import dateutil.relativedelta

from f1elo.db import Session
from f1elo.elo import Elo
from f1elo.model import *

class Interface:
    def __init__(self, date=None):
        self.session = Session()
        self.date = date

    def reset(self, date=None, _debug=False):
        if date is None:
            date = self.date

        query = self.session.query(Race)
        if date is not None:
            query = query.filter(Race.date > date)
        for race in query.all():
            race.ranked = False
            if _debug:
                print race

        query = self.session.query(Ranking)
        if date is not None:
            query = query.filter(Ranking.rank_date > date)
        query.delete()

        self.session.commit()

        if date is not None:
            date += datetime.timedelta(1)

        self.date = date

        return

    def rate(self, date=None, _debug=False):
        if date is None:
            date = self.date

        elo = Elo(self.session)
        race_query = self.session.query(Race).filter(Race.ranked == False)
        if date is not None:
            race_query = race_query.filter(Race.date <= date)
        races = race_query.order_by(Race.date).all()

        for race in races:
            if _debug:
                print race
                print

            ranks = elo.rank_race(race)
            driver_ranks = {}
            for entry, rank in ranks.iteritems():
                correction = rank / len(entry.drivers)
                for driver in entry.drivers:
                    if not driver_ranks.has_key(driver):
                        driver_ranks[driver] = 0;
                    driver_ranks[driver] += correction
            for driver, rank in driver_ranks.iteritems():
                ranking = Ranking()
                ranking.rank_date = race.date
                ranking.ranking = elo.get_ranking(driver, race.date) + rank
                self.session.add(ranking)
                driver.rankings.append(ranking)

            if _debug:
                for entry in race.entries:
                    print entry, elo.get_entry_ranking(entry, race.date), elo.get_entry_ranking(entry)
                print

            race.ranked = True
            date = race.date

        self.session.commit()

        self.date = date

        if self.date is not None:
            self.date += datetime.timedelta(1)

        return

    def fetch(self, date=None):
        if date is None:
            date = self.date
        if date is None:
            date = datetime.date.today()
            date += datetime.timedelta(1)

        one_year = dateutil.relativedelta.relativedelta(years=1)
        rankings = self.session.query(Ranking).filter(Ranking.rank_date > (date - one_year)).filter(Ranking.rank_date <= date).all()

        drivers = {}
        for ranking in rankings:
            if not drivers.has_key(ranking.driver):
                drivers[ranking.driver] = ranking.driver.get_ranking(date)

        self.date = date

        return sorted(drivers.values(), key=lambda rank: rank.ranking, reverse=True)
