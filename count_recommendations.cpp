//-------------------------------------------------------------------------------
// Filmaster - a social web network and recommendation engine
// Copyright (c) 2010 Filmaster (Borys Musielak, Adam Zielinski, Jakub Tlalka).
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as
// published by the Free Software Foundation, either version 3 of the
// License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.
//-------------------------------------------------------------------------------

//-------------------------------------------------------------------------------
//
// The film recommendation algorithm is documented on Filmaster wiki:
// http://filmaster.org/display/DEV/New+recommendation+engine
//
//-------------------------------------------------------------------------------

#include <cstdio>
#include <map>
#include <set>
#include <vector>
#include <ctime>
#include <cmath>
#include <algorithm>
#include <fstream>
#include <queue>
#include <cstring>
#define FOR(i,a,n) for(int i=a;i<=n;i++)
#define REP(i,n) for (int i=0;i<n;i++)
using namespace std;
typedef vector<int> vi;
typedef pair<int,int> pi;
typedef double dd;

const int featureNumber = 30, cycleNumber=50;
const dd baseRate = 6.7;
const dd stopRmse = 50.0;
const dd maxFeatureValue = 10.0;

int min_user_rates;
int min_film_rates;

dd baseUserValue, baseFilmValue;
dd baseLrate = 0.0001;
// ratings we already have and field for the guessed score
// user:        0
// film:        1
// given rate:  2
// guessed rate 3 (initially 5.0)
// backup rate  4
vector<dd> ratings[5];
// ratingsTemp contain guessed rating without including
// changes for presently computed feature
vector<dd> ratingsTemp;
// userValues[ft][u] - level of feature ft in user u
vector<dd> userValues[featureNumber+2];
// filmValues[ft][f] - level of feature ft in film f
vector<dd> filmValues[featureNumber+2];
// number of users ratings
vector<int> userRatingsNumber;
// number of film ratings
vector<int> filmRatingsNumber;
vector<int> userMap, filmMap;
dd rmse = 3.0;

int ratingsNumber, usersNumber, filmsNumber;

void backupFeatures(int feature){
    /* Backup features and restore them if something went wrong
     * during the teaching cycle */

    REP(u, usersNumber){
        userValues[featureNumber][u] = userValues[feature][u];
    }
    REP(f, filmsNumber)
        filmValues[featureNumber][f] = filmValues[feature][f];

    REP(rat, ratings[0].size())
        ratings[4][rat] = ratings[3][rat];
}

void restoreFeatures(int feature){
    REP(u, usersNumber)
        userValues[feature][u] = userValues[featureNumber][u];
    REP(f, filmsNumber)
        filmValues[feature][f] = filmValues[featureNumber][f];

    REP(rat, ratings[0].size())
        ratings[3][rat] = ratings[4][rat];
}

dd countrank(int u,int f){
    /* Compute actual score for a given pair (user,film) */

    dd score=0.0;
    REP(ft, featureNumber)
            score += userValues[ft][u] * filmValues[ft][f];
    if(score > 10.0) // the score can't exceed 10.0
        score = 10.0;
    if(score < 0.0) //the score can't be lower than 0.0
        score = 0.0;
    return score;
}

void readData(){
    /* Read the teaching data set */

    //read teaching ratings
    FILE *log = fopen("temp_data/new_recom.log", "a");
    FILE *fr = fopen("temp_data/ratings.in", "r");
    FILE *userMapFile = fopen("temp_data/userMap.in", "r");
    FILE *filmMapFile = fopen("temp_data/filmMap.in", "r");
    fscanf(fr, "%d %d %d %d %d\n", &ratingsNumber, &usersNumber, &filmsNumber,
            &min_user_rates, &min_film_rates);
    int film, user, rate;
    REP(u, usersNumber){
        fscanf(userMapFile, "%d", &user);
        userMap.push_back(user);
        userRatingsNumber.push_back(0);
    }
    REP(f, filmsNumber){
        fscanf(filmMapFile, "%d", &film);
        filmMap.push_back(film);
        filmRatingsNumber.push_back(0);
    }
    REP(i, ratingsNumber){
        fscanf(fr, "%d %d %d", &user, &film, &rate);
        ratings[0].push_back(user);
        ratings[1].push_back(film);
        ratings[2].push_back((dd)rate);
        ratings[3].push_back(baseRate);
        ratings[4].push_back(baseRate);
        // we count the sum and number of ranks for users and films
        userRatingsNumber[user] += 1;
        filmRatingsNumber[film] += 1;
    }

    REP(r, ratingsNumber)
        ratingsTemp.push_back(baseRate);
}

void init(void){
    /* Initialize data */

    FILE *log = fopen("temp_data/new_recom.log", "a");
    // the initial values of userValues and filmValues
    baseUserValue = baseFilmValue=sqrt(baseRate/featureNumber);
    // additional table used in algorithm,
    // containing temporary computed guessed rates
    REP(r, ratingsNumber){
        ratingsTemp[r] = baseRate;
        ratings[3][r] = baseRate;
    }
    fprintf(log, "count_recommendations.init: ratings prepared\n");
    //we initialize userValues and filmValues with baseUserValue
    REP(f, featureNumber+2){
        userValues[f].clear();
        filmValues[f].clear();
        REP(u, usersNumber)
            userValues[f].push_back(baseUserValue);
        REP(fm, filmsNumber)
            filmValues[f].push_back(baseFilmValue);
    }

    fprintf(log, "count_recommendations.init: initialization done\n");

}

void countRmse(int ft){
    /* we count the rmse after the teaching cycle */

    dd sumRmse = 0.0;
    // we count new guessed rates for the teaching ratings,
    // and compute control sum_rmse
        REP(rat, ratings[0].size()){
            dd add = userValues[ft][ratings[0][rat]] *
                    filmValues[ft][ratings[1][rat]];

            // we add result for present feature
            ratings[3][rat] = ratingsTemp[rat] + add -
                    baseUserValue * baseFilmValue;
            // computing sum_rmse
            sumRmse += pow(ratings[3][rat]-ratings[2][rat], 2);
        }
    rmse = sqrt(sumRmse/(dd)ratings[0].size());
}

void computeFeatures(int ft, dd lrate){
    // for every teaching rating we improve the userValues and filmValues
    REP(rat, ratings[0].size()){
        int u = ratings[0][rat], f = ratings[1][rat];

        // Difference between real rating and actual guessed rating scaled by
        // lrate. It is positive if the guessed rating is too low and
        // negative in opposite case
        dd err = lrate * (ratings[2][rat]-ratings[3][rat]);

        dd uv = userValues[ft][u];
        // we increase values if err is positive nad decrease in opposite case
        userValues[ft][u] += err * filmValues[ft][f];
        filmValues[ft][f] += err * uv ;
    }
}
void count(void){
    /* Main procedure, responsible for computing userValues and filmValues */

    FILE *log = fopen("temp_data/new_recom.log", "a");
    // we iterate through each feature

    // the previous rmse value, initially very high, if this value increases
    // after a teaching cycle, we terminate computing actual feature
    dd prev = 100.0;
    REP(ft,featureNumber){

        dd lrate = baseLrate * (dd)(ft+1);
        // we iterate through a cycleNumber number of teaching cycles
        REP(cyc, cycleNumber){
            backupFeatures(ft);
            computeFeatures(ft, lrate);
            countRmse(ft);

            // if the rmse increased we terminate computing this feature
            // if it is too big we have to moderate lrate
            if(rmse-prev > 0.01 || prev-rmse < 0.00000001 || rmse > stopRmse){
                restoreFeatures(ft);
                if(lrate < baseLrate)
                    break;

                lrate -= baseLrate;
                cyc --;
                continue;
            }
            prev = rmse;
        }

        REP(rat, ratings[0].size())
            ratingsTemp[rat] = ratings[3][rat];
    }
    fprintf(log, "count_recommendations.count: counting done\n");
}

void queries(void){
    /* Process queries of type (user,film) , computes the guessed rating for
     * this pair and creates the sql file to update the database
     * We'll be operating on the temporary table and in the end we will
       switch it to core_recommendation */

    FILE *log = fopen("temp_data/new_recom.log", "a");
    FILE *sw = fopen("temp_data/data_update.sql", "w");


    // we prepare the head of the sql file - data_update.sql
    // create a temp table
    fprintf(sw, "DROP TABLE temp_recommendation;\n");
    fprintf(sw, "CREATE TABLE temp_recommendation (id serial NOT NULL "
                "PRIMARY KEY, guess_rating_alg1 numeric(6, 4), "
                "guess_rating_alg2 numeric(6, 4), film_id integer, "
                "user_id integer);\n");

    // copy all new values at once for best performance
    fprintf(sw, "COPY temp_recommendation (guess_rating_alg2, user_id, film_id)"
                " FROM stdin;\n");

    // we read the query, compute the score and write to the sql file
    vector<pair<dd,int> > filmy;
    vector<int> users_with_recoms;

    // number of recommended movies for each user
    const int liczbaPolecanychFilmow = 8000;

    REP(user, userMap.size())
        // we count recommendations for users
        // who rated at least min_user_rates movies
        if(userRatingsNumber[user] >= min_user_rates){
            filmy.clear();
            REP(film, filmMap.size())
                // we consider movies that have at least
                // min_film_rates rates
                if(filmRatingsNumber[film] >= min_film_rates)
                  filmy.push_back(make_pair(
                              countrank(user,film), filmMap[film]));
            sort(filmy.begin(), filmy.end());
            if(filmy.size()) {
                users_with_recoms.push_back(userMap[user]);
            }
            for(int flm = filmy.size()-1; flm >= max(
                        (int)filmy.size()-liczbaPolecanychFilmow, 0); flm--)
                fprintf(sw,"%lf\t%d\t%d\n", filmy[flm].first,
                        userMap[user], filmy[flm].second);
        }

    fprintf(sw, "%c.\n", (char)92);
    fprintf(sw, "UPDATE core_profile set recommendations_status=0;\n");
    if(users_with_recoms.size()) {
        fprintf(sw, "UPDATE core_profile set recommendations_status=1 "
                    "where user_id in (");
        for(int i=0; i < users_with_recoms.size(); i++)
            fprintf(sw, "%s%d", i ? ", ":"", users_with_recoms[i]);
        fprintf(sw, ");\n");
    }


    // create indexes for the temp table
    fprintf(sw, "CREATE INDEX temp_recommendation_film_id ON "
                "temp_recommendation (film_id);\n");
    fprintf(log, "index temp_recommendation_film_id created;\n");
    fprintf(sw, "CREATE INDEX temp_recommendation_user_id ON "
                "temp_recommendation (user_id);\n");
    fprintf(log, "index temp_recommendation_user_id created;\n");
    fprintf(sw, "CREATE UNIQUE INDEX temp_recommendation_user_and_film ON "
                "temp_recommendation (user_id, film_id);\n");
    fprintf(log, "index temp_recommendation_user_and_film created;\n");

    // do the rest in transactions
//    fprintf(sw, "BEGIN;\n");
    // replace core_recommendation with temp_recommendation
    fprintf(sw, "DROP TABLE core_recommendation;\n");
    fprintf(log, "core_recommendation table dropped;\n");
    fprintf(sw, "ALTER TABLE temp_recommendation_id_seq RENAME TO "
                "core_recommendation_id_seq;\n");
    fprintf(log, "temp_recommendation_id_seq renamed to core_recommendation_id_seq;\n");
    fprintf(sw, "ALTER TABLE temp_recommendation RENAME TO "
                "core_recommendation;\n");
    fprintf(log, "core_recommendation table re-created;\n");
//    fprintf(sw, "END;\n");

    // rename indexes
    fprintf(sw, "ALTER INDEX temp_recommendation_film_id "
                "RENAME TO core_recommendation_film_id;\n");
    fprintf(sw, "ALTER INDEX temp_recommendation_user_id "
                "RENAME TO core_recommendation_user_id;\n");
    fprintf(sw, "ALTER INDEX temp_recommendation_user_and_film "
                "RENAME TO core_recommendation_user_and_film;\n");

    fprintf(log, "count_recommendations.queries: Queries written\n");
}

int main(){

    readData();
    do{
        init();
        count();
        baseLrate *= 0.95;
    }while(rmse > stopRmse);
    queries();

    return 0 ;
}

